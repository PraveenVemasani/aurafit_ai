"""
generator.py

AI-powered workout generator (AuraFit v1.1)

Focus:
- AI exercise selection
- AI explanation ("why this workout")
- AI sub-muscle balance analysis

Flow:
state -> planner -> rules -> AI -> workout
"""

import json
import os
from typing import Dict, List
import google.genai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from engine.state import UserState
from engine.planner import plan_day
from engine.rules import filter_allowed_exercises
from engine.exercises import EXERCISES
from db_helpers import get_recent_workouts
from config import get_secret


# -------------------------------------------------
# Gemini Client
# -------------------------------------------------
from google import genai
from config import get_secret

client = genai.Client(
    api_key=get_secret("GOOGLE_API_KEY")
)


# -------------------------------------------------
# Volume → exercise count (AuraFit v1 definition)
# -------------------------------------------------
VOLUME_TO_EXERCISES = {
    "moderate": 5,
    "light": 3,
    "very_light": 2,
    "rest": 0
}


# -------------------------------------------------
# AI Call Wrapper (exercise selection)
# -------------------------------------------------
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=20),
    stop=stop_after_attempt(3)
)

def _call_gemini_ids(prompt: str) -> List[str]:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )

    text = response.text.strip()
    data = json.loads(text)

    if not isinstance(data, list):
        raise ValueError("Gemini output is not a list")

    return data


# -------------------------------------------------
# AI Call Wrapper (analysis / explanation)
# -------------------------------------------------
def _call_gemini_text(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text.strip()

def summarize_training_history(workouts):
    summary = {
        "last_workout": None,
        "recent_muscle_usage": {},
        "recent_exercise_usage": {}
    }

    if not workouts:
        return summary

    # Most recent workout
    last = workouts[0]
    summary["last_workout"] = {
        "date": last["workout_date"],
        "primary_muscle": last["primary_muscle"],
        "exercises": last["exercise_ids"]
    }

    for w in workouts:
        muscle = w["primary_muscle"]
        summary["recent_muscle_usage"][muscle] = (
            summary["recent_muscle_usage"].get(muscle, 0) + 1
        )

        for ex_id in w["exercise_ids"]:
            summary["recent_exercise_usage"][ex_id] = (
                summary["recent_exercise_usage"].get(ex_id, 0) + 1
            )

    return summary

# -------------------------------------------------
# Main generator entry point
# -------------------------------------------------
def generate_workout(state: UserState, user_id: str) -> Dict:
    """
    Generates a workout using AI-driven coaching logic
    with cycle awareness and history summarization.
    """

    # 1️⃣ Load & summarize recent history
    recent_workouts = get_recent_workouts(user_id, days=7)
    history_summary = summarize_training_history(recent_workouts)

    # 2️⃣ Planner → intent (cycle-aware via history)
    plan = plan_day(state, history_summary)

    if plan.get("rest_day") or plan["volume"] == "rest":
        return {
            "rest_day": True,
            "reason": "Planned recovery day"
        }

    # 3️⃣ Hard safety rules
    allowed_exercises = filter_allowed_exercises(EXERCISES, state)

    # 4️⃣ RAG-lite narrowing
    candidates = [
        ex for ex in allowed_exercises
        if ex["primary_muscle"] == plan["primary_muscle"]
    ]

    if plan["primary_muscle"] == "legs" and plan.get("leg_section"):
        section = plan["leg_section"]
        section_specific = [
            ex for ex in candidates
            if section in ex.get("leg_section", [])
        ]
        if section_specific:
            candidates = section_specific

    if not candidates:
        return {
            "rest_day": True,
            "reason": "No safe exercises available"
        }

    # 5️⃣ AI prompt: exercise selection (cycle-aware)
    selection_prompt = f"""
You are a professional strength and conditioning coach.

GOAL:
- {state.goal}

TODAY'S TARGET:
- Primary muscle: {plan["primary_muscle"]}
- Volume: {plan["volume"]}

RECENT TRAINING SUMMARY:
- Last workout:
  {json.dumps(history_summary["last_workout"], indent=2)}

- Recent muscle usage (last 7 days):
  {json.dumps(history_summary["recent_muscle_usage"], indent=2)}

- Recent exercise usage:
  {json.dumps(history_summary["recent_exercise_usage"], indent=2)}

FATIGUE STATE:
{json.dumps(state.muscle_fatigue)}

IMPORTANT RULE:
Prioritize exercises where secondary/stabilizer muscles
(e.g., triceps during chest, lower back during rows)
are fresh based on the provided fatigue data
to avoid weak-link failure.

AVAILABLE EXERCISES (JSON):
{json.dumps(candidates, indent=2)}

TASK:
Return a JSON array of exercise IDs for today's workout.

INSTRUCTIONS:
- Avoid repeating exercises from the last session if possible
- Rotate angles and movement patterns
- Favor underused exercises
- Balance compound and isolation movements
- Output ONLY a JSON array
"""

    # 6️⃣ AI selects exercises
    try:
        selected_ids = _call_gemini_ids(selection_prompt)
        ai_used = True
    except Exception as e:
        print(f"⚠️ AI failed, fallback used. Reason: {e}")
        selected_ids = [ex["id"] for ex in candidates]
        ai_used = False

    # 7️⃣ Map IDs → exercises
    exercise_map = {ex["id"]: ex for ex in candidates}
    curated_exercises = [
        exercise_map[eid]
        for eid in selected_ids
        if eid in exercise_map
    ]

    # 8️⃣ Enforce volume
    max_exercises = VOLUME_TO_EXERCISES.get(plan["volume"], 3)
    curated_exercises = curated_exercises[:max_exercises]

    # 9️⃣ AI explanation (cycle-aware)
    explanation_prompt = f"""
You are a professional strength and conditioning coach.

Explain today's workout.

USER GOAL:
- {state.goal}

PRIMARY MUSCLE:
- {plan["primary_muscle"]}

LAST SESSION FOR THIS MUSCLE:
{json.dumps(history_summary["last_workout"], indent=2)}

EXERCISES TODAY:
{[ex["name"] for ex in curated_exercises]}

FATIGUE CONTEXT:
{state.muscle_fatigue}

Explain:
- Why this muscle was selected today
- How this session differs from the previous one
- How this supports progression and recovery

Be concise and practical.
"""

    ai_explanation = _call_gemini_text(explanation_prompt)

    # 🔟 AI sub-muscle balance analysis
    sub_muscle_prompt = f"""
Analyze the sub-muscle focus of today's workout.

PRIMARY MUSCLE:
- {plan["primary_muscle"]}

EXERCISES:
{json.dumps(curated_exercises, indent=2)}

Return JSON only:
{{
  "sub_muscle_focus": {{
    "<sub_muscle>": "<short emphasis description>"
  }}
}}
"""

    try:
        sub_muscle_focus = json.loads(_call_gemini_text(sub_muscle_prompt))
    except Exception:
        sub_muscle_focus = {}

    # 11️⃣ Final output
    return {
        "rest_day": False,
        "primary_muscle": plan["primary_muscle"],
        "volume": plan["volume"],
        "leg_section": plan.get("leg_section"),
        "ai_used": ai_used,
        "ai_explanation": ai_explanation,
        "sub_muscle_focus": sub_muscle_focus,
        "exercises": curated_exercises
    }

"""
planner.py

Decides training intent for the day:
- which primary muscle group
- optional leg section focus
- volume intent

NO exercise selection here.
NO AI here.
"""

from typing import Dict, Optional
from engine.state import UserState


# Order used when no better signal exists
DEFAULT_MUSCLE_ROTATION = [
    "chest",
    "back",
    "legs",
    "shoulders",
    "arms",
    "core",
]


def choose_primary_muscle(state: UserState) -> Optional[str]:
    """
    Pick the next muscle group to train.
    Skips muscles that are in pain.
    Chooses the least fatigued muscle otherwise.
    """

    candidates = []

    for muscle in DEFAULT_MUSCLE_ROTATION:
        if state.is_muscle_in_pain(muscle):
            continue

        fatigue = state.muscle_fatigue.get(muscle, 0)
        candidates.append((muscle, fatigue))

    if not candidates:
        return None  # full rest day

    # Pick muscle with lowest fatigue
    candidates.sort(key=lambda x: x[1])
    return candidates[0][0]


def choose_leg_section(state: UserState) -> Optional[str]:
    """
    If today is leg day, optionally focus on a leg section
    with the lowest fatigue.
    """

    leg_sections = ["quads", "hamstrings", "glutes", "calves", "adductors", "abductors"]

    section_fatigue = []

    for section in leg_sections:
        fatigue = state.muscle_fatigue.get(section, 0)
        section_fatigue.append((section, fatigue))

    section_fatigue.sort(key=lambda x: x[1])
    return section_fatigue[0][0]


def choose_volume(state: UserState, muscle: str) -> str:
    """
    Decide volume intent based on fatigue.
    """

    fatigue = state.muscle_fatigue.get(muscle, 0)

    if fatigue == 0:
        return "moderate"
    if fatigue == 1:
        return "light"
    if fatigue == 2:
        return "very_light"

    return "rest"


def plan_day(state: UserState, history_summary: dict) -> Dict:

    """
    Master planner output used by generator.py
    """

    primary_muscle = choose_primary_muscle(state)

    if primary_muscle is None:
        return {
            "rest_day": True
        }

    plan = {
        "rest_day": False,
        "primary_muscle": primary_muscle,
        "volume": choose_volume(state, primary_muscle),
        "leg_section": None
    }

    if primary_muscle == "legs":
        plan["leg_section"] = choose_leg_section(state)

    return plan

"""
feedback.py

Processes user feedback after a workout and updates UserState.
This is where learning happens (NO AI).
"""

from typing import List, Dict
from engine.state import UserState


def process_feedback(
    state: UserState,
    workout: Dict,
    feedback: List[Dict]
) -> None:
    """
    feedback format:
    [
        {
            "exercise_id": "barbell_bench_press",
            "status": "done" | "skipped",
            "reason": None | "missing_equipment" | "pain" | "not_in_mood" | "other"
        }
    ]
    """

    if workout.get("rest_day"):
        return

    exercises = {ex["id"]: ex for ex in workout.get("exercises", [])}

    for entry in feedback:
        ex_id = entry.get("exercise_id")
        status = entry.get("status")
        reason = entry.get("reason")

        if ex_id not in exercises:
            continue  # ignore invalid input safely

        ex = exercises[ex_id]
        primary_muscle = ex["primary_muscle"]

        # -------------------------
        # DONE
        # -------------------------
        if status == "done":
            state.increase_fatigue(primary_muscle)

            for eq in ex.get("equipment", []):
                state.equipment_available.add(eq)

        # -------------------------
        # SKIPPED
        # -------------------------
        if status == "skipped":
            state.skipped_exercises[ex_id] = (
                state.skipped_exercises.get(ex_id, 0) + 1
            )

            # Missing equipment → permanent learning
            if reason == "missing_equipment":
                for eq in ex.get("equipment", []):
                    state.equipment_unavailable.add(eq)

            # Pain → block muscle
            if reason == "pain":
                state.mark_muscle_pain(primary_muscle)

            # not_in_mood / other → analytics only (v1)

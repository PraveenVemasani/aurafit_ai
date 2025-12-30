"""
rules.py

Hard safety and feasibility rules for the AuraFit AI engine.
NO AI, NO randomness, NO side effects.
"""

from typing import List, Dict
from engine.state import UserState


def is_equipment_allowed(exercise: Dict, state: UserState) -> bool:
    """
    Returns False if any required equipment is known to be unavailable.
    """
    for eq in exercise.get("equipment", []):
        if eq in state.equipment_unavailable:
            return False
    return True


def is_muscle_allowed(exercise: Dict, state: UserState) -> bool:
    """
    Returns False if the primary muscle is in pain
    or conflicts with known health issues.
    """
    primary = exercise.get("primary_muscle")

    if state.is_muscle_in_pain(primary):
        return False

    if primary in state.health_issues:
        return False

    return True


def is_fatigue_allowed(exercise: Dict, state: UserState, fatigue_limit: int = 3) -> bool:
    """
    Simple fatigue guard:
    if a muscle is already highly fatigued, avoid it.
    """
    primary = exercise.get("primary_muscle")
    fatigue = state.muscle_fatigue.get(primary, 0)

    return fatigue < fatigue_limit


def is_exercise_allowed(
    exercise: Dict,
    state: UserState,
    fatigue_limit: int = 3
) -> bool:
    """
    Master rule check.
    ALL conditions must pass.
    """
    return (
        is_equipment_allowed(exercise, state)
        and is_muscle_allowed(exercise, state)
        and is_fatigue_allowed(exercise, state, fatigue_limit)
    )


def filter_allowed_exercises(
    exercises: List[Dict],
    state: UserState,
    fatigue_limit: int = 3
) -> List[Dict]:
    """
    Filters the full exercise list down to only safe & feasible exercises.
    """
    allowed = []

    for ex in exercises:
        if is_exercise_allowed(ex, state, fatigue_limit):
            allowed.append(ex)

    return allowed

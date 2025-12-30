"""
state.py

Defines the persistent learning state for the AuraFit AI engine.
This file contains NO logic — only state representation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class UserState:
    # -------------------------
    # Basic profile
    # -------------------------
    height_cm: int
    weight_kg: int
    goal: str                     # muscle_gain | weight_loss | recomp
    health_issues: List[str]      # knee_pain, back_pain, etc.

    # -------------------------
    # Equipment learning
    # -------------------------
    equipment_available: Set[str] = field(default_factory=set)
    equipment_unavailable: Set[str] = field(default_factory=set)

    # -------------------------
    # Muscle intelligence
    # -------------------------
    muscle_fatigue: Dict[str, int] = field(default_factory=dict)
    muscle_flags: Dict[str, str] = field(default_factory=dict)
    # example: {"legs": "pain"}

    # -------------------------
    # History / analytics (v1 simple)
    # -------------------------
    skipped_exercises: Dict[str, int] = field(default_factory=dict)

    # -------------------------
    # Helpers (safe defaults)
    # -------------------------
    def is_muscle_in_pain(self, muscle: str) -> bool:
        return self.muscle_flags.get(muscle) == "pain"

    def mark_muscle_pain(self, muscle: str):
        self.muscle_flags[muscle] = "pain"

    def clear_muscle_pain(self, muscle: str):
        if muscle in self.muscle_flags:
            del self.muscle_flags[muscle]

    def increase_fatigue(self, muscle: str):
        self.muscle_fatigue[muscle] = self.muscle_fatigue.get(muscle, 0) + 1

    def reset_fatigue(self):
        self.muscle_fatigue.clear()

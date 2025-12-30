# db_helpers.py
from datetime import date
from typing import Dict

from db import supabase
from engine.state import UserState


# -------------------------
# USER
# -------------------------

def get_or_create_user(username: str) -> str:
    """
    Returns user_id for a given username.
    Creates user + user_state if not exists.
    """
    res = supabase.table("users").select("*").eq("name", username).execute()

    if res.data:
        return res.data[0]["id"]

    # Create user
    user = supabase.table("users").insert({
        "name": username
    }).execute()

    user_id = user.data[0]["id"]

    # Create empty state row
    supabase.table("user_state").insert({
        "user_id": user_id
    }).execute()

    return user_id


# -------------------------
# LOAD STATE
# -------------------------

def load_user_state(user_id: str) -> UserState:
    res = supabase.table("user_state").select("*").eq("user_id", user_id).single().execute()
    data = res.data

    return UserState(
        height_cm=175,
        weight_kg=72,
        goal="muscle_gain",
        health_issues=[],

        muscle_fatigue=data.get("muscle_fatigue", {}),
        muscle_flags=data.get("muscle_flags", {}),
        equipment_available=set(data.get("equipment_available", [])),
        equipment_unavailable=set(data.get("equipment_unavailable", [])),
        skipped_exercises=data.get("skipped_exercises", {})
    )


# -------------------------
# SAVE STATE
# -------------------------

def save_user_state(user_id: str, state: UserState):
    supabase.table("user_state").update({
        "muscle_fatigue": state.muscle_fatigue,
        "muscle_flags": state.muscle_flags,
        "equipment_available": list(state.equipment_available),
        "equipment_unavailable": list(state.equipment_unavailable),
        "skipped_exercises": state.skipped_exercises
    }).eq("user_id", user_id).execute()


# -------------------------
# SAVE WORKOUT SUMMARY
# -------------------------

def save_workout_summary(user_id: str, workout: Dict):
    if workout.get("rest_day"):
        return

    supabase.table("workout_history").insert({
        "user_id": user_id,
        "workout_date": date.today().isoformat(),
        "primary_muscle": workout["primary_muscle"],
        "volume": workout["volume"],
        "exercise_ids": [ex["id"] for ex in workout["exercises"]],
        "ai_used": workout.get("ai_used", True)
    }).execute()


# -------------------------
# LOAD WORKOUT HISTORY
# -------------------------

def load_workout_history(user_id: str, limit: int = 10):
    res = (
        supabase
        .table("workout_history")
        .select("*")
        .eq("user_id", user_id)
        .order("workout_date", desc=True)
        .limit(limit)
        .execute()
    )

    return res.data or []

# History Summarizer

def get_recent_workouts(user_id: str, days: int = 7):
    res = (
        supabase
        .table("workout_history")
        .select("*")
        .eq("user_id", user_id)
        .order("workout_date", desc=True)
        .limit(days)
        .execute()
    )
    return res.data or []

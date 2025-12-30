# app.py
import streamlit as st

from engine.generator import generate_workout
from engine.feedback import process_feedback
from engine.state import UserState

from db_helpers import (
    get_or_create_user,
    load_user_state,
    save_user_state,
    save_workout_summary,
    load_workout_history
)

# -------------------------------------------------
# App Config
# -------------------------------------------------
st.set_page_config(page_title="AuraFit AI", layout="centered")
st.title("🏋️ AuraFit AI Trainer")
st.caption("AI-powered workouts that adapt over time")


# -------------------------------------------------
# User Selection
# -------------------------------------------------
st.sidebar.header("User")

username = st.sidebar.text_input("Enter your name")

if not username:
    st.info("Please enter your name to continue.")
    st.stop()


# -------------------------------------------------
# Load user + state (ONCE)
# -------------------------------------------------
if "user_id" not in st.session_state:
    st.session_state.user_id = get_or_create_user(username)
    st.session_state.state = load_user_state(st.session_state.user_id)
    st.session_state.workout = None

state: UserState = st.session_state.state
user_id: str = st.session_state.user_id


# -------------------------------------------------
# Profile Controls (minimal)
# -------------------------------------------------
st.sidebar.header("Goal")

state.goal = st.sidebar.selectbox(
    "Training Goal",
    ["muscle_gain", "weight_loss", "recomp"],
    index=["muscle_gain", "weight_loss", "recomp"].index(state.goal)
)

# -------------------------------------------------
# Sidebar: Workout History (FIXED)
# -------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("📅 Workout History")

history = load_workout_history(user_id, limit=7)

if not history:
    st.sidebar.caption("No past workouts yet.")
else:
    for w in history:
        with st.sidebar.expander(
            f"{w['workout_date']} • {w['primary_muscle'].title()}",
            expanded=False  # 👈 important
        ):
            st.markdown(f"**Volume:** {w['volume']}")
            st.markdown("**Exercises:**")

            for ex_id in w["exercise_ids"]:
                st.markdown(f"- {ex_id}")


# -------------------------------------------------
# Generate Workout
# -------------------------------------------------
if st.button("Generate Today's Workout"):
    st.session_state.workout = generate_workout(state, st.session_state.user_id)

workout = st.session_state.workout


# -------------------------------------------------
# Display Workout
# -------------------------------------------------
if workout:
    if workout.get("rest_day"):
        st.warning("🛌 Rest Day")
        st.write(workout.get("reason"))
    else:
        st.subheader("Today's Workout")

        st.markdown(f"**Primary Muscle:** {workout['primary_muscle']}")
        st.markdown(f"**Volume:** {workout['volume']}")

        if workout.get("leg_section"):
            st.markdown(f"**Leg Section:** {workout['leg_section']}")

        st.markdown("### Exercises")

        feedback_inputs = []

        for ex in workout["exercises"]:
            with st.container():
                st.markdown(f"### {ex['name']}")

                # Tip & Caution (from exercises.py)
                if ex.get("tip"):
                    st.success(f"✅ **Tip:** {ex['tip']}")

                if ex.get("caution"):
                    st.warning(f"⚠️ **Caution:** {ex['caution']}")

                status = st.radio(
                    f"Status – {ex['id']}",
                    ["done", "skipped"],
                    horizontal=True,
                    key=f"status_{ex['id']}"
                )

                reason = None
                if status == "skipped":
                    reason = st.selectbox(
                        "Reason",
                        ["missing_equipment", "pain", "not_in_mood", "other"],
                        key=f"reason_{ex['id']}"
                    )

                feedback_inputs.append({
                    "exercise_id": ex["id"],
                    "status": status,
                    "reason": reason
                })

        # AI Explanation
        if workout.get("ai_explanation"):
            st.markdown("### 🤖 Why this workout?")
            st.info(workout["ai_explanation"])

        # Sub-muscle focus
        if workout.get("sub_muscle_focus"):
            st.markdown("### 🎯 Sub-muscle Focus")
            for k, v in workout["sub_muscle_focus"].items():
                st.write(f"**{k}** — {v}")

        # -------------------------------------------------
        # Submit Feedback
        # -------------------------------------------------
        if st.button("Submit Feedback"):
            process_feedback(state, workout, feedback_inputs)

            save_user_state(user_id, state)
            save_workout_summary(user_id, workout)

            st.success("Feedback saved. Your AI trainer just got smarter 💪")

            with st.expander("🔍 Internal State (Debug)"):
                st.json({
                    "muscle_fatigue": state.muscle_fatigue,
                    "muscle_pain": state.muscle_flags,
                    "equipment_unavailable": list(state.equipment_unavailable),
                    "skipped_exercises": state.skipped_exercises
                })


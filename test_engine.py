"""
test_engine.py

Full manual test harness for AuraFit AI Engine v1.
Uses AI-powered generator (Gemini).

Focuses on:
- State reconciliation (pain + equipment)
- Planner behavior
- AI workout curation
- Feedback loop
- State evolution over days
"""

from engine.state import UserState
from engine.generator import generate_workout
from engine.feedback import process_feedback


# -------------------------------------------------
# STATE RECONCILIATION HELPERS
# -------------------------------------------------
def reconcile_pain_state(state):
    if not state.muscle_flags:
        return

    print("\n--- PAIN CHECK-IN ---")

    resolved = []
    for muscle, status in state.muscle_flags.items():
        if status != "pain":
            continue

        ans = input(f"Is your {muscle} pain-free today? (y/n): ").strip().lower()
        if ans == "y":
            resolved.append(muscle)

    for muscle in resolved:
        state.clear_muscle_pain(muscle)
        print(f"✓ Cleared pain flag for {muscle}")


def reconcile_equipment_state(state):
    print("\n--- EQUIPMENT CHECK-IN ---")

    if state.equipment_unavailable:
        print("\nCurrently unavailable equipment:")
        for eq in state.equipment_unavailable:
            print(f"- {eq}")

        ans = input("Is this list still correct? (y/n): ").strip().lower()

        if ans == "n":
            restored = []
            for eq in list(state.equipment_unavailable):
                confirm = input(f"Is '{eq}' available again? (y/n): ").strip().lower()
                if confirm == "y":
                    restored.append(eq)

            for eq in restored:
                state.equipment_unavailable.remove(eq)
                state.equipment_available.add(eq)
                print(f"✓ Marked '{eq}' as available")

    ans = input("Any NEW unavailable equipment today? (y/n): ").strip().lower()

    if ans == "y":
        while True:
            eq = input("Enter equipment name (or press Enter to stop): ").strip().lower()
            if not eq:
                break
            state.equipment_unavailable.add(eq)
            print(f"✓ Marked '{eq}' as unavailable")


# -------------------------------------------------
# UTIL
# -------------------------------------------------

def print_workout(workout):
    if workout.get("rest_day"):
        print("\n===== REST DAY =====")
        print("Reason:", workout.get("reason"))
        return

    print("\n===== TODAY'S WORKOUT =====")
    print("Primary muscle:", workout["primary_muscle"])
    print("Volume:", workout["volume"])

    if workout.get("leg_section"):
        print("Leg section:", workout["leg_section"])

    for ex in workout["exercises"]:
        print("-", ex["name"])

    # 🔹 NEW: AI explanation
    if workout.get("ai_explanation"):
        print("\nWHY THIS WORKOUT:")
        print(workout["ai_explanation"])

    # 🔹 NEW: Sub-muscle focus
    if workout.get("sub_muscle_focus"):
        print("\nSUB-MUSCLE FOCUS:")
        for k, v in workout["sub_muscle_focus"].items():
            print(f"- {k}: {v}")

# -------------------------------------------------
# MAIN TEST LOOP
# -------------------------------------------------
def run_simulation():
    state = UserState(
        height_cm=175,
        weight_kg=72,
        goal="muscle_gain",
        health_issues=[]
    )

    day = 1

    while True:
        print("\n==============================")
        print(f"         DAY {day}")
        print("==============================")

        # 1️⃣ Reconcile persistent state
        reconcile_pain_state(state)
        reconcile_equipment_state(state)

        # 2️⃣ Generate workout using AI
        workout = generate_workout(state)
        print_workout(workout)

        if workout.get("rest_day"):
            ans = input("\nContinue to next day? (y/n): ").strip().lower()
            if ans != "y":
                break
            day += 1
            continue

        # 3️⃣ Collect feedback
        feedback = []

        print("\n--- WORKOUT FEEDBACK ---")
        for ex in workout["exercises"]:
            print(f"\nExercise: {ex['name']}")
            status = input("Status (done/skip): ").strip().lower()

            if status == "done":
                feedback.append({
                    "exercise_id": ex["id"],
                    "status": "done",
                    "reason": None
                })
            else:
                reason = input(
                    "Reason (missing_equipment / pain / not_in_mood / other): "
                ).strip().lower()

                feedback.append({
                    "exercise_id": ex["id"],
                    "status": "skipped",
                    "reason": reason
                })

        # 4️⃣ Process feedback → learning
        process_feedback(state, workout, feedback)

        # 5️⃣ State snapshot
        print("\n--- STATE SNAPSHOT ---")
        print("Muscle fatigue:", state.muscle_fatigue)
        print("Muscle pain:", state.muscle_flags)
        print("Unavailable equipment:", state.equipment_unavailable)
        print("Skipped exercises:", state.skipped_exercises)

        ans = input("\nContinue to next day? (y/n): ").strip().lower()
        if ans != "y":
            break

        day += 1


if __name__ == "__main__":
    run_simulation()

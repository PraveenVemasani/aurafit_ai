from collections import defaultdict
from engine.exercises import EXERCISES


def summary_by_muscle_and_difficulty():
    """
    Prints:
    ===== EXERCISES BY PRIMARY MUSCLE =====
    Chest       : beginner: X, intermediate: Y, advanced: Z
    Back        : beginner: X, intermediate: Y, advanced: Z
    ...
    """

    # muscle -> difficulty -> count
    stats = defaultdict(lambda: defaultdict(int))

    for ex in EXERCISES:
        muscle = ex["primary_muscle"]
        difficulty = ex["difficulty"]
        stats[muscle][difficulty] += 1

    print("\n===== EXERCISES BY PRIMARY MUSCLE =====\n")

    for muscle in ["chest", "back", "legs", "shoulders", "arms", "core"]:
        beginner = stats[muscle].get("beginner", 0)
        intermediate = stats[muscle].get("intermediate", 0)
        advanced = stats[muscle].get("advanced", 0)

        print(
            f"{muscle.capitalize():<12}: "
            f"beginner: {beginner}, "
            f"intermediate: {intermediate}, "
            f"advanced: {advanced}"
        )
    eq=[]
    for ex in EXERCISES:
        if len(ex["equipment"])>1:
            eq.append(ex["equipment"][0])
            eq.append(ex["equipment"][1])
        else:
            eq.append(ex["equipment"][0])
    print("\n===== EQUIPMENT LIST =====\n")
    equipment_set = set(eq)
    print(equipment_set)

if __name__ == "__main__":
    summary_by_muscle_and_difficulty()

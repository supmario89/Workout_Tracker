import csv
import datetime
import json
import os

chest_workout = ["Bench", "Incline Bench"]
arms_workout = ["Hammer Curls", "Tricep Dumbells"]

workout_groups = {
    "Chest/Back": chest_workout,
    "Arms": arms_workout
}

def get_workout_data(muscle_group, today):
    results = []
    for exercise in muscle_group:
        weight = input(f"Input weight for {exercise}: ")
        reps1 = input(f"Input reps for set 1 of {exercise}: ")
        reps2 = input(f"Input reps for set 2 of {exercise}: ")
        reps3 = input(f"Input reps for set 3 of {exercise}: ")
        results.append({"date": today, "exercise": exercise, "weight": weight, "reps1": reps1, "reps2": reps2, "reps3": reps3})

    with open("latest_workout.json", "w") as f:
        json.dump(results, f, indent=4)
    print("Workout saved to latest_workout.json")
    return results

def update_csv(results, workout_day):
    if workout_day == "Chest/Back":
        file_name = "chest&back_workout.csv"
    elif workout_day == "Arms":
        file_name = "arms_workout.csv"
    else:
        return

    file_path = os.path.join("workout_csvs", file_name)

    # --- gather previous weights per exercise ---
    last_weight_by_exercise = {}
    if os.path.exists(file_path):
        with open(file_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                exercise_name = row.get("Exercise")
                weight_value = row.get("Weight", "")
                if exercise_name:
                    last_weight_by_exercise[exercise_name] = weight_value

    # --- augment each new result with change columns ---
    for entry in results:
        # Weight change vs. previous workout
        prev_weight = last_weight_by_exercise.get(entry["exercise"])
        try:
            current_wt = float(entry["weight"])
            prev_wt = float(prev_weight) if prev_weight not in ("", None) else None
        except ValueError:
            current_wt, prev_wt = None, None

        if prev_wt is None:
            entry["weight_change"] = "N/A"
        else:
            diff_wt = current_wt - prev_wt
            entry["weight_change"] = "no change" if diff_wt == 0 else f"{diff_wt:+g} lbs"

        # Reps3 change vs. baseline of 8
        try:
            reps3_val = int(entry["reps3"])
        except ValueError:
            reps3_val = None

        if reps3_val is None:
            entry["reps3_change"] = "N/A"
        else:
            diff_rep = reps3_val - 8
            entry["reps3_change"] = "no change" if diff_rep == 0 else f"{diff_rep:+d} reps"

    # ensure headers include the new keys
    if results:
        headers = results[0].keys()
    else:
        headers = []

    with open(file_path, "a", newline='') as file:
        csv_writer = csv.DictWriter(file, fieldnames=headers)
        csv_writer.writerows(results)

def main():
    workout_day = input("Pick what workout day it is [Chest/Back] or [Arms]: ")
    today = datetime.date.today().isoformat()
    print(today)

    muscle_group = workout_groups.get(workout_day)
    if not muscle_group:
        print("Invalid workout day.")
        return

    results = get_workout_data(muscle_group, today)
    update_csv(results, workout_day)

if __name__ == "__main__":
    main()

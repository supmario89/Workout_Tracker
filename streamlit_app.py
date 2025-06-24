import datetime
import csv
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import json

WORKOUT_JSON_PATH = "workout_days.json"
if os.path.exists(WORKOUT_JSON_PATH):
    with open(WORKOUT_JSON_PATH, "r") as f:
        workout_groups = json.load(f)
else:
    workout_groups = {
        "Chest/Back": ["Bench", "Incline Bench"],
        "Arms": ["Hammer Curls", "Tricep Dumbells"]
    }
    with open(WORKOUT_JSON_PATH, "w") as f:
        json.dump(workout_groups, f, indent=2)

workout_days = list(workout_groups.keys())

def update_csv(results, workout_day):
    file_name = f"{workout_day.lower().replace(' ', '_')}_workout.csv"

    file_path = os.path.join("workout_csvs", file_name)

    last_weight_by_exercise = {}
    if os.path.exists(file_path):
        with open(file_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                exercise_name = row.get("Exercise")
                weight_value = row.get("Weight", "")
                if exercise_name:
                    last_weight_by_exercise[exercise_name] = weight_value

    for entry in results:
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

        try:
            reps3_val = int(entry["reps3"])
        except ValueError:
            reps3_val = None

        if reps3_val is None:
            entry["reps3_change"] = "N/A"
        else:
            diff_rep = reps3_val - 8
            entry["reps3_change"] = "no change" if diff_rep == 0 else f"{diff_rep:+d} reps"

    if results:
        headers = results[0].keys()
    else:
        headers = []

    with open(file_path, "a", newline='') as file:
        csv_writer = csv.DictWriter(file, fieldnames=headers)
        csv_writer.writerows(results)

workout_days = list(workout_groups.keys())
def make_sidebar(current_page):
    with st.sidebar:
        if current_page == "Home":
            st.title("Home Page Sidebar")
            st.write("Welcome to the Home page!")
        elif current_page == "Tracker":
            st.title("Tracker Page Sidebar")
            st.write("View your workout progress trends.")
        # No sidebar for unspecified pages

st.title("Workout Tracker")
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .stButton>button {
            border-radius: 8px;
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        .stTextInput>div>div>input {
            border-radius: 5px;
        }
        @media (max-width: 768px) {
            .stButton>button {
                width: 100%;
            }
            .stTextInput {
                width: 100% !important;
            }
            .stTextArea, .stSelectbox, .stNumberInput {
                width: 100% !important;
            }
            .stExpander {
                margin-bottom: 1rem;
            }
        }
    </style>
""", unsafe_allow_html=True)

def Home_page():
    
    visit = st.selectbox("Select Workout Day:", list(workout_days))

    if visit:
        exercise_data = {}
        st.subheader(f"Exercises for {visit} day")
        for exercise in workout_groups.get(visit, []):
            with st.expander(exercise):
                weight = st.text_input("Weight", key=exercise)
                reps1 = st.text_input("Reps1", key=f"Reps1{exercise}", placeholder=8)
                reps2 = st.text_input("Reps2", key=f"Reps2{exercise}", placeholder=8)
                reps3 = st.text_input("Reps3", key=f"Reps3{exercise}", placeholder=8)
                # Store data in a dict
                exercise_data[exercise] = {
                    "weight": weight,
                    "reps1": reps1,
                    "reps2": reps2,
                    "reps3": reps3
                }

        if st.button("Save workout to CSV"):
            results = []
            today = datetime.date.today().isoformat()
            for exercise, data in exercise_data.items():
                results.append({
                    "date": today,
                    "exercise": exercise,
                    "weight": data["weight"],
                    "reps1": data["reps1"] if data["reps1"] else "8",
                    "reps2": data["reps2"] if data["reps2"] else "8",
                    "reps3": data["reps3"] if data["reps3"] else "8"
                })
            update_csv(results, visit)
            st.success("Workout saved!")

            
def Tracker_page():
    make_sidebar("Tracker")
    st.title("Progress Tracker")

    folder = "workout_csvs"
    if not os.path.exists(folder):
        st.info("No workout data folder found.")
        return

    for file_name in os.listdir(folder):
        if not file_name.endswith("_workout.csv"):
            continue

        workout_day = file_name.replace("_workout.csv", "").replace("_", " ").title()
        file_path = os.path.join(folder, file_name)

        if not os.path.exists(file_path):
            st.info(f"No data for {workout_day} yet.")
            continue

        df = pd.read_csv(file_path)
        if df.empty or len(df.columns) <= 1:
            continue
        df.columns = [c.lower() for c in df.columns]
        if "date" not in df.columns or "exercise" not in df.columns or "weight" not in df.columns:
            st.warning(f"CSV for {workout_day} missing required columns.")
            continue
        df["date"] = pd.to_datetime(df["date"])
        latest_dates = df["date"].drop_duplicates().sort_values(ascending=False).head(10).tolist()
        filtered = df[df["date"].isin(latest_dates)]

        prs = df.groupby("exercise")["weight"].max().to_dict()

        with st.sidebar:
            st.markdown(f"### {workout_day} PRs")
            for exercise, weight in prs.items():
                st.markdown(f"- 🏅 **{exercise}**: {weight} lbs")

        st.subheader(f"{workout_day} Trends")
        pivot_df = filtered.pivot_table(index="date", columns="exercise", values="weight", aggfunc="first").reset_index()
        melted = pivot_df.melt(id_vars=["date"], var_name="exercise", value_name="weight")

        fig = px.line(
            melted,
            x="date",
            y="weight",
            color="exercise",
            markers=True,
            title=f"{workout_day} - Weight Trends",
            labels={"weight": "Weight (lbs)", "date": "Date"}
        )
        fig.update_traces(mode="lines+markers", hovertemplate="%{x}<br>%{y} lbs<extra>%{fullData.name}</extra>")
        st.plotly_chart(fig, use_container_width=True)

def Builder_page():
    make_sidebar("Builder")
    st.title("Workout Builder")

    new_day = st.text_input("Name your workout day (e.g., Legs, Push, Pull)")
    exercise_list = st.text_area("Enter exercises, one per line")

    if st.button("Save Workout Day"):
        if not new_day or not exercise_list.strip():
            st.error("Please provide a workout name and at least one exercise.")
            return

        exercises = [e.strip() for e in exercise_list.strip().split("\n") if e.strip()]
        if not exercises:
            st.error("You must enter at least one valid exercise.")
            return

        workout_groups[new_day] = exercises

        # Create a new CSV file with standard headers
        file_name = new_day.lower().replace(" ", "_") + "_workout.csv"
        file_path = os.path.join("workout_csvs", file_name)
        if not os.path.exists("workout_csvs"):
            os.makedirs("workout_csvs")
        if not os.path.exists(file_path):
            with open(file_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["date", "exercise", "weight", "reps1", "reps2", "reps3", "weight_change", "reps3_change"])
                writer.writeheader()

        with open(WORKOUT_JSON_PATH, "w") as f:
            json.dump(workout_groups, f, indent=2)

        st.success(f"Workout day '{new_day}' created with {len(exercises)} exercises.")

page = st.sidebar.radio("Go to:", ["Home", "Tracker", "Builder", "Edit Workouts"])

if page == "Home":
    Home_page()
elif page == "Tracker":
    Tracker_page()
elif page == "Builder":
    Builder_page()
elif page == "Edit Workouts":
    def Edit_page():
        make_sidebar("Edit Workouts")
        st.title("Edit or Delete Workout")


        selected_day = st.selectbox("Select workout day to edit", list(workout_groups.keys()))
        if not selected_day:
            return

        # Initialize session state for exercises if needed (per selection)
        if "edit_exercises" not in st.session_state or st.session_state.get("selected_day") != selected_day:
            st.session_state["selected_day"] = selected_day
            st.session_state["edit_exercises"] = workout_groups.get(selected_day, []).copy()

        # Add a new exercise using on_change
        def add_new_exercise():
            new_ex = st.session_state.get("new_exercise_input", "").strip()
            if new_ex and new_ex not in st.session_state["edit_exercises"]:
                st.session_state["edit_exercises"].append(new_ex)
                workout_groups[selected_day] = st.session_state["edit_exercises"]
                with open(WORKOUT_JSON_PATH, "w") as f:
                    json.dump(workout_groups, f, indent=2)
                st.success("Exercise added.")

        new_exercise = st.text_input("Add a new exercise", key="new_exercise_input")
        if st.button("Add Exercise"):
            add_new_exercise()

        # Use exercises from session state
        exercises = st.session_state["edit_exercises"]

        st.subheader("Reorder or Remove Exercises")

        modified = False
        for i, ex in enumerate(exercises):
            col1, col2, col3, col4 = st.columns([6, 1, 1, 1])
            col1.write(ex)
            if col2.button("↑", key=f"up_{i}") and i > 0:
                exercises[i], exercises[i - 1] = exercises[i - 1], exercises[i]
                modified = True
            if col3.button("↓", key=f"down_{i}") and i < len(exercises) - 1:
                exercises[i], exercises[i + 1] = exercises[i + 1], exercises[i]
                modified = True
            if col4.button("❌", key=f"remove_{i}"):
                exercises.pop(i)
                modified = True
                break  # Re-render needed

        if modified:
            st.session_state["edit_exercises"] = exercises
            workout_groups[selected_day] = exercises
            with open(WORKOUT_JSON_PATH, "w") as f:
                json.dump(workout_groups, f, indent=2)
            st.rerun()

        if st.button(f"Delete '{selected_day}' workout day", type="primary"):
            del workout_groups[selected_day]
            with open(WORKOUT_JSON_PATH, "w") as f:
                json.dump(workout_groups, f, indent=2)
            csv_name = f"{selected_day.lower().replace(' ', '_')}_workout.csv"
            csv_path = os.path.join("workout_csvs", csv_name)
            if os.path.exists(csv_path):
                os.remove(csv_path)
            st.warning(f"'{selected_day}' workout and CSV deleted.")
    Edit_page()

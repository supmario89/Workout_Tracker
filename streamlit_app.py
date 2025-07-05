def populate_sample_data():
    import random
    from datetime import timedelta

    sample_exercises = ["Bench Press", "Incline Press", "Lat Pulldown", "Rows", "Pec Deck"]
    base_date = datetime.date.today()

    for i in range(5):
        day_offset = timedelta(days=-i*2)
        workout_date = (base_date + day_offset).isoformat()
        for ex in sample_exercises:
            entry = {
                "date": workout_date,
                "exercise": ex,
                "weight": str(random.randint(100, 200)),
                "reps1": str(random.randint(6, 10)),
                "reps2": str(random.randint(6, 10)),
                "reps3": str(random.randint(6, 10)),
                "workout_day": "Push"
            }
            db.collection("users").document(user_id).collection("workout_results").add(entry)

    st.success("Sample workout data added.")
import datetime
import csv
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import firebase_admin
from firebase_admin import credentials, firestore

 # --- User authentication block ---
USER_CREDENTIALS = {
    "Mario": "Mario",
    "Joseph": "Joseph"
}

if "user_id" not in st.session_state:
    login_container = st.empty()
    with login_container:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        login_btn = st.button("Login", key="login_button")

        if login_btn:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state["user_id"] = username
                st.rerun()
            else:
                st.error("Invalid username or password.")
    st.stop()

user_id = st.session_state["user_id"]

if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        "private_key": st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["firebase"]["client_email"],
        "client_id": st.secrets["firebase"]["client_id"],
        "auth_uri": st.secrets["firebase"]["auth_uri"],
        "token_uri": st.secrets["firebase"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        "universe_domain": st.secrets["firebase"]["universe_domain"]
    })
    firebase_admin.initialize_app(cred)
db = firestore.client()

def load_workout_groups():
    docs = db.collection("users").document(user_id).collection("workout_groups").stream()
    return {doc.id: doc.to_dict()["exercises"] for doc in docs}

def save_workout_group(name, exercises):
    db.collection("users").document(user_id).collection("workout_groups").document(name).set({"exercises": exercises})

def delete_workout_group(name):
    db.collection("users").document(user_id).collection("workout_groups").document(name).delete()

workout_groups = load_workout_groups()

workout_days = list(workout_groups.keys())

def update_csv(results, workout_day):
    for entry in results:
        doc_ref = db.collection("users").document(user_id).collection("workout_results").document()
        doc_ref.set({**entry, "workout_day": workout_day})

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


    if st.button("Go to Builder"):
        st.session_state["page"] = "Builder"
        st.rerun()

    if visit:
        exercise_data = {}
        st.subheader(f"Exercises for {visit} day")
        for exercise in workout_groups.get(visit, []):
            ex_name = exercise["name"] if isinstance(exercise, dict) else exercise
            docs = db.collection("users").document(user_id).collection("workout_results").where("exercise", "==", ex_name).stream()
            max_weight = ""
            try:
                weights = [float(doc.to_dict().get("weight", 0)) for doc in docs if doc.to_dict().get("weight")]
                if weights:
                    max_weight = str(int(max(weights)))
            except:
                pass
            num_sets = exercise.get("sets", 3) if isinstance(exercise, dict) else 3
            with st.expander(ex_name):
                weight_key = f"weight_{ex_name}"
                weight = st.text_input(
                    "Weight",
                    key=weight_key,
                    placeholder=max_weight
                )
                reps_inputs = []
                for i in range(num_sets):
                    rep_key = f"Reps{i+1}_{ex_name}"
                    rep_val = st.text_input(
                        f"Reps{i+1}",
                        key=rep_key,
                        placeholder="8"
                    )
                    reps_inputs.append(rep_val)
                exercise_data[ex_name] = {
                    "weight": weight,
                    "reps": [r if r else "8" for r in reps_inputs]
                }

        if st.button("End Workout"):
            results = []
            today = datetime.date.today().isoformat()
            for exercise, data in exercise_data.items():
                entry = {
                    "date": today,
                    "exercise": exercise,
                    "weight": data["weight"],
                }
                for i, r in enumerate(data["reps"]):
                    entry[f"reps{i+1}"] = r
                results.append(entry)
            update_csv(results, visit)
            for key in list(st.session_state.keys()):
                if key.startswith("weight_") or key.startswith("Reps"):
                    del st.session_state[key]
            st.success("Workout saved!")
            
def Tracker_page():
    make_sidebar("Tracker")
    st.title("Progress Tracker")

    docs = db.collection("users").document(user_id).collection("workout_results").stream()
    all_data = [doc.to_dict() for doc in docs]
    if not all_data:
        st.info("No workout data found.")
        return
    df = pd.DataFrame(all_data)
    df["date"] = pd.to_datetime(df["date"])
    for workout_day in df["workout_day"].unique():
        wdf = df[df["workout_day"] == workout_day]
        if wdf.empty:
            continue
        st.subheader(f"{workout_day} Trends")
        prs = wdf.groupby("exercise")["weight"].max().to_dict()
        with st.sidebar:
            st.markdown(f"### {workout_day} PRs")
            for exercise, weight in prs.items():
                st.markdown(f"- 🏅 **{exercise}**: {weight} lbs")
        latest_dates = wdf["date"].drop_duplicates().sort_values(ascending=False).head(10).tolist()
        filtered = wdf[wdf["date"].isin(latest_dates)]
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
    default_reps = st.number_input("Number of sets per exercise", min_value=1, max_value=10, value=3, help="Defaults to 3 sets if left unchanged")

    if st.button("Save Workout Day"):
        if not new_day or not exercise_list.strip():
            st.error("Please provide a workout name and at least one exercise.")
            return

        exercises = [{"name": e.strip(), "sets": default_reps} for e in exercise_list.strip().split("\n") if e.strip()]
        if not exercises:
            st.error("You must enter at least one valid exercise.")
            return

        save_workout_group(new_day, exercises)
        st.success(f"Workout day '{new_day}' created with {len(exercises)} exercises.")

if "page" not in st.session_state:
    st.session_state["page"] = "Home"

# Sidebar: show logged-in user and log out button
with st.sidebar:
    st.markdown(f"**Logged in as:** {st.session_state['user_id']}")
    if st.button("Log Out"):
        st.session_state.clear()
        st.rerun()

page = st.sidebar.radio("Go to:", ["Home", "Tracker", "Builder", "Edit Workouts", "Manage Data"], index=["Home", "Tracker", "Builder", "Edit Workouts", "Manage Data"].index(st.session_state["page"]))

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
                save_workout_group(selected_day, workout_groups[selected_day])
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
            display_name = ex["name"] if isinstance(ex, dict) else ex
            col1.write(display_name)
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
            save_workout_group(selected_day, exercises)
            st.rerun()

        if st.button(f"Delete '{selected_day}' workout day", type="primary"):
            delete_workout_group(selected_day)
            csv_name = f"{selected_day.lower().replace(' ', '_')}_workout.csv"
            csv_path = os.path.join("workout_csvs", csv_name)
            if os.path.exists(csv_path):
                os.remove(csv_path)
            st.warning(f"'{selected_day}' workout and CSV deleted.")
    Edit_page()
elif page == "Manage Data":
    def Manage_data_page():
        make_sidebar("Manage Data")
        st.title("Manage Workout Data")

        docs = db.collection("users").document(user_id).collection("workout_results").stream()
        entries = [doc for doc in docs]
        if not entries:
            st.info("No workout data found.")
            return

        workout_logs = [{"id": doc.id, **doc.to_dict()} for doc in entries]
        df = pd.DataFrame(workout_logs)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=False)

        for row in df.itertuples():
            with st.expander(f"{row.date.date()} - {row.workout_day} - {row.exercise}"):
                st.write(f"Weight: {row.weight}")
                rep_cols = sorted([col for col in df.columns if col.startswith("reps")], key=lambda x: int(x[4:]))
                for col in rep_cols:
                    val = getattr(row, col, None)
                    if val:
                        st.write(f"{col.capitalize()}: {val}")
                if hasattr(row, "notes") and row.notes:
                    st.markdown(f"**Notes:** {row.notes}")
                if st.button("Delete Entry", key=row.id):
                    db.collection("users").document(user_id).collection("workout_results").document(row.id).delete()
                    st.success("Workout session deleted.")
                    st.rerun()
    Manage_data_page()

# if user_id == "Mario":
#     populate_sample_data()

import streamlit as st
import json

# Load vaccine data
with open("vaccines_full_schedule copy.json", "r") as f:
    data = json.load(f)

st.title("Baby Vaccine Tracker")
st.image("baby_photo.jpg")

visit = st.selectbox("Select Doctor Visit:", list(data.keys()))

if visit:
    st.subheader(f"Vaccines for {visit}")
    for vaccine, details in data[visit].items():
        with st.expander(vaccine):
            # st.markdown("**Glances**")
            # for glance in details["glances"]:
            #     st.markdown(f"-{glance}")
            st.markdown("**Pros:**")
            for pro in details["pros"]:
                st.markdown(f"- {pro}")
            st.markdown("**Cons:**")
            for con in details["cons"]:
                st.markdown(f"- {con}")

            choice = st.radio(f"Accept {vaccine}?", ["undecided", "yes", "no"], index=["undecided", "yes", "no"].index(details["status"]))
            if choice != details["status"]:
                data[visit][vaccine]["status"] = choice
                with open("vaccines_full_schedule copy.json", "w") as f:
                    json.dump(data, f, indent=2)
                st.success(f"Updated {vaccine} status to: {choice}")

yes_list = []
no_list = []

# Loop through all visits and vaccines
for visit, vaccines in data.items():
    for vaccine, details in vaccines.items():
        if details["status"] == "yes":
            yes_list.append(f"{visit}: {vaccine}")
        elif details["status"] == "no":
            no_list.append(f"{visit}: {vaccine}")

# Display lists
st.sidebar.subheader("✅ Accepted Vaccines")
for v in yes_list:
    st.sidebar.markdown(f"- {v}")

st.sidebar.subheader("❌ Declined Vaccines")
for v in no_list:
    st.sidebar.markdown(f"- {v}")
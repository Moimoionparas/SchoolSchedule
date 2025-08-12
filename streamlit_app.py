import streamlit as st
import pandas as pd

# Example weekdays list
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

def schedule_editor(username):
    # Load or initialize the schedule for the user
    if f"{username}_schedule" not in st.session_state:
        # Sample initial schedule DataFrame
        df = pd.DataFrame({
            "Weekday": ["Monday", "Monday", "Tuesday"],
            "Break": [False, True, False],
            "Class Number": [1, 2, 1],
            "Class Time": ["8:00-8:45", "8:45-9:00", "8:00-8:45"],
            "Subject": ["Math", "", "English"],
            "Teacher": ["Mr. A", "", "Ms. B"],
        })
        st.session_state[f"{username}_schedule"] = df
    else:
        df = st.session_state[f"{username}_schedule"]

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Weekday": {"type": "category", "options": WEEKDAYS},
            "Break": {"type": "bool"},
            # other columns are editable as default (text or number)
        }
    )

    st.session_state[f"{username}_schedule"] = edited_df
    st.write("Your schedule:")
    st.dataframe(edited_df)


def main():
    st.title("School Schedule")

    # For demo purpose, just a username in session_state
    if "username" not in st.session_state:
        st.session_state["username"] = "max.jamia"  # Example logged-in user

    schedule_editor(st.session_state["username"])

if __name__ == "__main__":
    main()

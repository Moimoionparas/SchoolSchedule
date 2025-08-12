import streamlit as st
import pandas as pd

# --------- Helper Functions ---------
def verify_credentials(username, password):
    users = st.secrets["users"]
    return username in users and users[username]["password"] == password

def verify_pin(username, pin):
    users = st.secrets["users"]
    return username in users and users[username]["pin"] == pin

def load_schedule(username):
    if username not in st.session_state["schedules"]:
        # Initialize default empty schedule for new users
        st.session_state["schedules"][username] = pd.DataFrame({
            "Weekday": [],
            "Class Number": [],
            "Class Name": [],
            "Teacher": [],
            "Start Time": [],
            "End Time": [],
            "Break": []
        })
    return st.session_state["schedules"][username]

def save_schedule(username, df):
    st.session_state["schedules"][username] = df

# --------- Main Functions ---------
def login():
    st.title("Login")
    st.write("Please login with your username/password or PIN.")

    login_method = st.radio("Login method", ["Username/Password", "PIN"])

    if login_method == "Username/Password":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if verify_credentials(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

    else:
        username_pin = st.text_input("Username")
        pin = st.text_input("PIN", type="password")
        if st.button("Login"):
            if verify_pin(username_pin, pin):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username_pin
                st.experimental_rerun()
            else:
                st.error("Invalid username or PIN")

def logout():
    if st.button("Logout"):
        for key in ["logged_in", "username"]:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()

def schedule_editor(username):
    st.title(f"Schedule Editor - {username}")
    df = load_schedule(username)

    # Editable schedule table using st.data_editor
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Weekday": st.column_config.Selectbox(
                "Weekday", options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            ),
            "Class Number": st.column_config.Number(
                "Class Number", min_value=1, max_value=20
            ),
            "Class Name": st.column_config.Text("Class Name"),
            "Teacher": st.column_config.Text("Teacher"),
            "Start Time": st.column_config.Text("Start Time (HH:MM)"),
            "End Time": st.column_config.Text("End Time (HH:MM)"),
            "Break": st.column_config.Checkbox("Break"),
        },
    )

    save_schedule(username, edited_df)
    st.success("Schedule saved!")
    logout()

def main():
    # Initialize schedules dict if not exists
    if "schedules" not in st.session_state:
        st.session_state["schedules"] = {}

    # Keep user logged in on refresh
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""

    if not st.session_state["logged_in"]:
        login()
    else:
        schedule_editor(st.session_state["username"])

if __name__ == "__main__":
    main()

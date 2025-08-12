import streamlit as st
import pandas as pd
import json
import os

# --- Constants ---
ADMIN_USERNAME = "max.jamia"
ADMIN_PASSWORD = "Ruokapoyta!"
DATA_DIR = "user_data"
USERS_FILE = "users.json"  # local users + PIN storage for demo

# --- Helpers ---

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    else:
        users = {}
        if "users" in st.secrets:
            for u, pwd in st.secrets["users"].items():
                users[u] = {"password": pwd, "pin": st.secrets.get("pins", {}).get(u, "")}
        return users

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_schedule(username):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    path = os.path.join(DATA_DIR, f"{username}_schedule.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return pd.read_json(f)
    else:
        # Default schedule example as a DataFrame
        data = {
            "Weekday": ["Monday", "Monday", "Tuesday", "Tuesday", "Wednesday"],
            "Class Number": [1, 2, 1, 2, 1],
            "Class Time": ["08:00 - 09:00", "09:15 - 10:15", "08:00 - 09:00", "09:15 - 10:15", "08:00 - 09:00"],
            "Subject": ["Math", "Physics", "Chemistry", "Biology", "Math"],
            "Teacher": ["Smith", "Johnson", "Lee", "Davis", "Smith"],
            "Break": [False, True, False, True, False]
        }
        df = pd.DataFrame(data)
        return df

def save_schedule(username, df):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    path = os.path.join(DATA_DIR, f"{username}_schedule.json")
    df.to_json(path, orient="records")

def authenticate(username, password, users):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return True, "admin"
    if username in users and users[username]["password"] == password:
        return True, "user"
    return False, None

def authenticate_pin(pin, users):
    if pin == ADMIN_PASSWORD:  # Admin PIN same as password for simplicity
        return True, ADMIN_USERNAME, "admin"
    for u, creds in users.items():
        if creds.get("pin") == pin and creds.get("pin") != "":
            return True, u, "user"
    return False, None, None

# --- Main app ---

def login(users):
    st.title("Login")
    method = st.radio("Login method:", ["Username/Password", "PIN"])

    if method == "Username/Password":
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            valid, role = authenticate(username, password, users)
            if valid:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = role
                st.success(f"Welcome {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    else:
        pin = st.text_input("Enter PIN", type="password", key="login_pin")
        if st.button("Login with PIN"):
            valid, username, role = authenticate_pin(pin, users)
            if valid:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = role
                st.success(f"Welcome {username}!")
                st.rerun()
            else:
                st.error("Invalid PIN")

def logout():
    if st.sidebar.button("Logout"):
        for key in ["logged_in", "username", "role"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

def admin_panel(users):
    st.sidebar.header("Admin Panel")
    st.sidebar.write("Manage users and schedules")

    with st.sidebar.expander("Add User"):
        new_user = st.text_input("New username", key="new_user")
        new_pass = st.text_input("New password", type="password", key="new_pass")
        new_pin = st.text_input("New PIN", key="new_pin")
        if st.button("Add user", key="add_user"):
            if new_user in users or new_user == ADMIN_USERNAME:
                st.error("User already exists")
            elif not new_user:
                st.error("Username cannot be empty")
            else:
                users[new_user] = {"password": new_pass, "pin": new_pin}
                save_users(users)
                st.success(f"User '{new_user}' added")

    with st.sidebar.expander("Remove User"):
        if users:
            remove_user = st.selectbox("Select user to remove", [u for u in users.keys()], key="remove_user_select")
            if st.button("Remove user", key="remove_user"):
                if remove_user in users:
                    del users[remove_user]
                    save_users(users)
                    st.success(f"User '{remove_user}' removed")
        else:
            st.write("No users to remove")

    st.sidebar.subheader("Current users")
    for u, creds in users.items():
        st.sidebar.write(f"- {u} (PIN: {creds.get('pin', '')})")

def schedule_editor(username):
    st.title(f"{username}'s Schedule")

    df = load_schedule(username)

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Weekday": st.column_config.Selectbox(
                options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                label="Weekday"
            ),
            "Break": st.column_config.Checkbox(label="Break"),
            "Class Number": st.column_config.Number(label="Class Number", min_value=1),
            "Class Time": st.column_config.Text(label="Class Time"),
            "Subject": st.column_config.Text(label="Subject"),
            "Teacher": st.column_config.Text(label="Teacher")
        }
    )

    if st.button("Save Schedule"):
        save_schedule(username, edited_df)
        st.success("Schedule saved!")

def main():
    users = load_users()

    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        login(users)
    else:
        st.sidebar.write(f"Logged in as: {st.session_state['username']}")
        logout()

        if st.session_state["role"] == "admin":
            admin_panel(users)

        schedule_editor(st.session_state["username"])

if __name__ == "__main__":
    main()

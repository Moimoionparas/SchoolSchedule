import streamlit as st
import json
import os

# --- Constants ---
ADMIN_USERNAME = "max.jamia"
ADMIN_PASSWORD = "Ruokapoyta!"
DATA_DIR = "user_data"
USERS_FILE = "users.json"  # local users + PIN storage for demo

# --- Helpers ---

def load_users():
    # Load users + passwords + PINs from a JSON file (simulate editable secrets)
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    else:
        # start with secrets users + pins from st.secrets
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
            return json.load(f)
    else:
        # default empty schedule: subjects with empty day lists
        return {
            "Math": [],
            "Physics": [],
            "Chemistry": [],
            "Biology": []
        }

def save_schedule(username, schedule):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    path = os.path.join(DATA_DIR, f"{username}_schedule.json")
    with open(path, "w") as f:
        json.dump(schedule, f, indent=2)

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
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
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
        pin = st.text_input("Enter PIN", type="password")
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
    if st.button("Logout"):
        for key in ["logged_in", "username", "role"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

def admin_panel(users):
    st.sidebar.header("Admin Panel")
    st.sidebar.write("Manage users and schedules")

    # Add user
    with st.sidebar.expander("Add User"):
        new_user = st.text_input("New username")
        new_pass = st.text_input("New password", type="password")
        new_pin = st.text_input("New PIN")
        if st.button("Add user"):
            if new_user in users or new_user == ADMIN_USERNAME:
                st.error("User already exists")
            else:
                users[new_user] = {"password": new_pass, "pin": new_pin}
                save_users(users)
                st.success(f"User '{new_user}' added")

    # Remove user
    with st.sidebar.expander("Remove User"):
        remove_user = st.selectbox("Select user to remove", [u for u in users.keys()])
        if st.button("Remove user"):
            if remove_user in users:
                del users[remove_user]
                save_users(users)
                st.success(f"User '{remove_user}' removed")

    # List users
    st.sidebar.subheader("Current users")
    for u, creds in users.items():
        st.sidebar.write(f"- {u} (PIN: {creds.get('pin', '')})")

def schedule_editor(username):
    st.title(f"{username}'s Schedule")

    schedule = load_schedule(username)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # Editable schedule: for each subject, select multiple days
    for subject in schedule.keys():
        selected_days = st.multiselect(f"Select days for {subject}", options=days, default=schedule[subject])
        schedule[subject] = selected_days

    if st.button("Save Schedule"):
        save_schedule(username, schedule)
        st.success("Schedule saved")

    # Display current schedule summary
    st.write("### Current Schedule")
    for subject, days_list in schedule.items():
        st.write(f"{subject}: {', '.join(days_list) if days_list else 'No days assigned'}")

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

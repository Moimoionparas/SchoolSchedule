import streamlit as st
import pandas as pd

# --------- Helper Functions ---------
def verify_credentials(username, password):
    # Hardcoded users for demo
    users = {
        "max.jamia": {"password": "Ruokapoyta!", "pin": "051713"},
        "user1": {"password": "password1", "pin": "1234"},
    }
    return username in users and users[username]["password"] == password

def verify_pin(username, pin):
    users = {
        "max.jamia": {"password": "Ruokapoyta!", "pin": "051713"},
        "user1": {"password": "password1", "pin": "1234"},
    }
    return username in users and users[username]["pin"] == pin

def load_schedule(username):
    if username not in st.session_state["schedules"]:
        # Initialize empty schedule
        st.session_state["schedules"][username] = pd.DataFrame({
            "Viikonpäivä": [],
            "Tunti": [],
            "Aihe": [],
            "Opettaja": [],
            "Alkuaika": [],
            "Loppuaika": [],
            "Tauko": []
        })
    return st.session_state["schedules"][username]

def save_schedule(username, df):
    st.session_state["schedules"][username] = df

# --------- Main Functions ---------
def login():
    st.title("Kirjaudu sisään")
    st.write("Kirjaudu käyttäjätunnuksella/salasanalla tai PIN-koodilla.")

    login_method = st.radio("Kirjautumistapa", ["Käyttäjätunnus/Salasana", "PIN-koodi"])

    if login_method == "Käyttäjätunnus/Salasana":
        username = st.text_input("Käyttäjätunnus")
        password = st.text_input("Salasana", type="password")
        if st.button("Kirjaudu"):
            if verify_credentials(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["rerun_trigger"] = not st.session_state.get("rerun_trigger", False)
            else:
                st.error("Virheellinen käyttäjätunnus tai salasana")

    else:
        username_pin = st.text_input("Käyttäjätunnus")
        pin = st.text_input("PIN-koodi", type="password")
        if st.button("Kirjaudu"):
            if verify_pin(username_pin, pin):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username_pin
                st.session_state["rerun_trigger"] = not st.session_state.get("rerun_trigger", False)
            else:
                st.error("Virheellinen käyttäjätunnus tai PIN-koodi")

def logout():
    if st.button("Kirjaudu ulos"):
        for key in ["logged_in", "username"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["rerun_trigger"] = not st.session_state.get("rerun_trigger", False)

def schedule_editor():
    username = st.session_state.get("username", "")
    st.title(f"Aikataulun muokkaus - {username}")
    df = load_schedule(username)

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Viikonpäivä": st.column_config.Selectbox(
                "Viikonpäivä",
                options=["Maanantai", "Tiistai", "Keskiviikko", "Torstai", "Perjantai", "Lauantai", "Sunnuntai"]
            ),
            "Tunti": st.column_config.Number(
                "Tunti", min_value=1, max_value=20
            ),
            "Aihe": st.column_config.Text("Aihe"),
            "Opettaja": st.column_config.Text("Opettaja"),
            "Alkuaika": st.column_config.Text("Alkuaika (HH:MM)"),
            "Loppuaika": st.column_config.Text("Loppuaika (HH:MM)"),
            "Tauko": st.column_config.Checkbox("Tauko"),
        },
    )

    save_schedule(username, edited_df)
    st.success("Aikataulu tallennettu!")
    logout()

def main():
    if "schedules" not in st.session_state:
        st.session_state["schedules"] = {}

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""

    if not st.session_state["logged_in"]:
        login()
    else:
        schedule_editor()

if __name__ == "__main__":
    main()

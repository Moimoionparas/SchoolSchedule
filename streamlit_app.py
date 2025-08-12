import streamlit as st
import pandas as pd

# --- Hardcoded users ---
USERS = {
    "max.jamia": {"password": "Ruokapoyta!", "pin": "051713"},
    "user1": {"password": "salasana1", "pin": "1234"},
    "user2": {"password": "salasana2", "pin": "5678"},
}

# --- Authentication helpers ---
def verify_credentials(username, password):
    return username in USERS and USERS[username]["password"] == password

def verify_pin(username, pin):
    return username in USERS and USERS[username]["pin"] == pin

# --- Schedule helpers ---
def load_schedule(username):
    if "schedules" not in st.session_state:
        st.session_state["schedules"] = {}
    if username not in st.session_state["schedules"]:
        st.session_state["schedules"][username] = pd.DataFrame({
            "Viikonpäivä": [],
            "Tuntinumero": [],
            "Aihe": [],
            "Opettaja": [],
            "Alkuaika": [],
            "Loppuaika": [],
            "Tauko": []
        })
    return st.session_state["schedules"][username]

def save_schedule(username, df):
    st.session_state["schedules"][username] = df

# --- UI pages ---
def login_page():
    st.title("Kirjautuminen")
    st.write("Kirjaudu sisään käyttäjätunnuksella/salasanalla tai PIN-koodilla.")

    login_method = st.radio("Kirjautumistapa", ["Käyttäjätunnus/Salasana", "PIN-koodi"])

    login_success = False
    username = ""

    if login_method == "Käyttäjätunnus/Salasana":
        username_input = st.text_input("Käyttäjätunnus", key="username_input")
        password_input = st.text_input("Salasana", type="password", key="password_input")
        if st.button("Kirjaudu sisään"):
            if verify_credentials(username_input, password_input):
                login_success = True
                username = username_input
            else:
                st.error("Virheellinen käyttäjätunnus tai salasana")

    else:  # PIN login
        username_pin = st.text_input("Käyttäjätunnus", key="username_pin_input")
        pin_input = st.text_input("PIN-koodi", type="password", key="pin_input")
        if st.button("Kirjaudu sisään"):
            if verify_pin(username_pin, pin_input):
                login_success = True
                username = username_pin
            else:
                st.error("Virheellinen käyttäjätunnus tai PIN-koodi")

    if login_success:
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.rerun()

def logout_button():
    if st.button("Kirjaudu ulos"):
        for key in ["logged_in", "username"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

def schedule_editor():
    username = st.session_state["username"]
    st.title(f"Aikataulun muokkaus - {username}")

    df = load_schedule(username)

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Viikonpäivä": st.column_config.Selectbox(
                "Viikonpäivä", options=["Maanantai", "Tiistai", "Keskiviikko", "Torstai", "Perjantai", "Lauantai", "Sunnuntai"]
            ),
            "Tuntinumero": st.column_config.Number(
                "Tuntinumero", min_value=1, max_value=20
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

    logout_button()

# --- Main ---
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""

    if st.session_state["logged_in"]:
        schedule_editor()
    else:
        login_page()

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd

# --- Users (hardcoded, no secrets) ---
USERS = {
    "max.jamia": {"password": "Ruokapoyta!", "pin": "051713"},
    "user1": {"password": "salasana1", "pin": "1234"},
    "user2": {"password": "salasana2", "pin": "5678"},
}

# --- Helper functions ---
def verify_credentials(username, password):
    return username in USERS and USERS[username]["password"] == password

def verify_pin(username, pin):
    return username in USERS and USERS[username]["pin"] == pin

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

# --- Login page ---
def login():
    st.title("Kirjautuminen")
    st.write("Kirjaudu sisään käyttäjätunnuksella/salasanalla tai PIN-koodilla.")

    login_method = st.radio("Kirjautumistapa", ["Käyttäjätunnus/Salasana", "PIN-koodi"])

    if login_method == "Käyttäjätunnus/Salasana":
        username = st.text_input("Käyttäjätunnus", key="username_input")
        password = st.text_input("Salasana", type="password", key="password_input")
        if st.button("Kirjaudu sisään"):
            if verify_credentials(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success("Kirjautuminen onnistui!")
            else:
                st.error("Virheellinen käyttäjätunnus tai salasana")

    else:  # PIN login
        username_pin = st.text_input("Käyttäjätunnus", key="username_pin_input")
        pin = st.text_input("PIN-koodi", type="password", key="pin_input")
        if st.button("Kirjaudu sisään"):
            if verify_pin(username_pin, pin):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username_pin
                st.success("Kirjautuminen onnistui!")
            else:
                st.error("Virheellinen käyttäjätunnus tai PIN-koodi")

# --- Logout button ---
def logout():
    if st.button("Kirjaudu ulos"):
        for key in ["logged_in", "username"]:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()  # This should be fine here if your Streamlit supports it

# --- Schedule editor ---
def schedule_editor(username):
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
    logout()

# --- Main ---
def main():
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

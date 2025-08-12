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
    if "schedules" not in st.session_state:
        st.session_state["schedules"] = {}
    if username not in st.session_state["schedules"]:
        # Alusta tyhjä aikataulu uusille käyttäjille
        st.session_state["schedules"][username] = pd.DataFrame({
            "Viikonpäivä": [],
            "Tunnin numero": [],
            "Oppiaine": [],
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
                st.experimental_rerun()
            else:
                st.error("Virheellinen käyttäjätunnus tai salasana")

    else:
        username_pin = st.text_input("Käyttäjätunnus", key="username_pin_input")
        pin = st.text_input("PIN-koodi", type="password", key="pin_input")
        if st.button("Kirjaudu sisään"):
            if verify_pin(username_pin, pin):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username_pin
                st.experimental_rerun()
            else:
                st.error("Virheellinen käyttäjätunnus tai PIN-koodi")

def logout():
    if st.button("Kirjaudu ulos"):
        for key in ["logged_in", "username"]:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()

def schedule_editor(username):
    st.title(f"Aikataulun muokkaus - {username}")
    df = load_schedule(username)

    # Muokattava aikataulutaulukko st.data_editorilla
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Viikonpäivä": st.column_config.Selectbox(
                "Viikonpäivä", options=["Maanantai", "Tiistai", "Keskiviikko", "Torstai", "Perjantai", "Lauantai", "Sunnuntai"]
            ),
            "Tunnin numero": st.column_config.Number(
                "Tunnin numero", min_value=1, max_value=20
            ),
            "Oppiaine": st.column_config.Text("Oppiaine"),
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
    # Alusta kirjautumistila, jos ei vielä ole
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

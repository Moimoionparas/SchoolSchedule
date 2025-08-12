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
                st.stop()
            else:
                st.error("Virheellinen käyttäjätunnus tai salasana")

    else:
        username_pin = st.text_input("Käyttäjätunnus", key="username_pin_input")
        pin = st.text_input("PIN-koodi", type="password", key="pin_input")
        if st.button("Kirjaudu sisään"):
            if verify_pin(username_pin, pin):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username_pin
                st.stop()
            else:
                st.error("Virheellinen käyttäjätunnus tai PIN-koodi")

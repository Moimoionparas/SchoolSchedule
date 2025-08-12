import streamlit as st
import sqlite3
import bcrypt
from datetime import time

DB_NAME = "users.db"

def luo_tietokanta():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def lisaa_käyttäjä(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("Käyttäjätunnus on jo olemassa!")
    conn.close()

def tarkista_kirjautuminen(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        password_hash = row[0]
        return bcrypt.checkpw(password.encode(), password_hash)
    return False

# Lukujärjestys oletusdata
DEFAULT_TIMETABLE = {
    "Maanantai": [],
    "Tiistai": [],
    "Keskiviikko": [],
    "Torstai": [],
    "Perjantai": []
}

def kirjautuminen():
    st.title("Kirjaudu sisään")

    valinta = st.radio("Valitse", ["Kirjaudu sisään", "Rekisteröidy"])

    if valinta == "Rekisteröidy":
        uusi_käyttäjä = st.text_input("Uusi käyttäjätunnus")
        uusi_salasana = st.text_input("Uusi salasana", type="password")
        uusi_salasana2 = st.text_input("Toista salasana", type="password")
        if st.button("Rekisteröidy"):
            if uusi_salasana != uusi_salasana2:
                st.error("Salasanat eivät täsmää")
            elif len(uusi_salasana) < 4:
                st.error("Salasana liian lyhyt")
            elif uusi_käyttäjä.strip() == "":
                st.error("Käyttäjätunnus ei voi olla tyhjä")
            else:
                lisaa_käyttäjä(uusi_käyttäjä.strip(), uusi_salasana)
                st.success("Rekisteröityminen onnistui! Kirjaudu sisään.")
    else:
        käyttäjä = st.text_input("Käyttäjätunnus")
        salasana = st.text_input("Salasana", type="password")
        if st.button("Kirjaudu"):
            if tarkista_kirjautuminen(käyttäjä, salasana):
                st.session_state['kirjautunut'] = True
                st.session_state['käyttäjä'] = käyttäjä
                st.success(f"Tervetuloa, {käyttäjä}!")
                st.experimental_rerun()
            else:
                st.error("Virheellinen käyttäjätunnus tai salasana")

def tuntien_lisays(timetable):
    st.header("Lisää tunti lukujärjestykseen")
    päivä = st.selectbox("Valitse viikonpäivä", list(timetable.keys()))
    aine = st.text_input("Aine")
    luokka = st.text_input("Luokan numero")
    opettaja = st.text_input("Opettajan nimi")
    alku = st.time_input("Tunnin alku", time(8, 0))
    loppu = st.time_input("Tunnin loppu", time(8, 45))
    välitunti = st.checkbox("Välitunti?")

    if st.button("Lisää tunti"):
        if välitunti:
            aine = "Välitunti"
            opettaja = ""
            luokka = ""
        tunti = {
            "aine": aine,
            "luokka": luokka,
            "opettaja": opettaja,
            "alku": alku,
            "loppu": loppu,
            "välitunti": välitunti
        }
        timetable[päivä].append(tunti)
        st.success(f"Tunti lisätty {päivä}lle")

def nayta_lukujärjestys(timetable):
    st.header("Viikon lukujärjestys")
    for päivä, tunnit in timetable.items():
        st.subheader(päivä)
        if not tunnit:
            st.write("Ei tunteja lisättynä.")
        else:
            for t in sorted(tunnit, key=lambda x: x['alku']):
                aika = f"{t['alku'].strftime('%H:%M')} - {t['loppu'].strftime('%H:%M')}"
                if t["välitunti"]:
                    st.write(f"{aika} - Välitunti")
                else:
                    st.write(f"{aika} - {t['aine']} (Luokka {t['luokka']}, Opettaja: {t['opettaja']})")

def app():
    luo_tietokanta()

    if 'kirjautunut' not in st.session_state:
        st.session_state['kirjautunut'] = False

    if not st.session_state['kirjautunut']:
        kirjautuminen()
        return

    if 'timetable' not in st.session_state:
        st.session_state['timetable'] = DEFAULT_TIMETABLE.copy()

    st.sidebar.title(f"Tervetuloa, {st.session_state['käyttäjä']}!")
    valinta = st.sidebar.radio("Valitse toiminto", ["Näytä lukujärjestys", "Lisää tunti", "Kirjaudu ulos"])

    if valinta == "Näytä lukujärjestys":
        nayta_lukujärjestys(st.session_state['timetable'])
    elif valinta == "Lisää tunti":
        tuntien_lisays(st.session_state['timetable'])
    elif valinta == "Kirjaudu ulos":
        st.session_state['kirjautunut'] = False
        st.experimental_rerun()

if __name__ == "__main__":
    app()

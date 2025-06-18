import streamlit as st
from modules import poutre, dalle, accueil, profile

PAGES = {
    "Accueil": accueil,
    "Poutre béton armé": poutre,
    "Dalle béton armé": dalle,
    "Profilé métallique": profile
}

st.sidebar.title("Menu")
selection = st.sidebar.radio("Aller à", list(PAGES.keys()))

page = PAGES[selection]
page.show()

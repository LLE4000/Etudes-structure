import streamlit as st
from modules import (
    accueil,
    poutre,
    dalle,
    profile_metal,
    tableau_armatures,
    recouvrement,
    choix_profile,
    flambement,
    tableau_profiles
)

# 🔁 Lecture du paramètre dans l'URL
page = st.query_params.get("page", ["Accueil"])[0]
st.session_state.page = page

# 🖼️ Configuration de la page
st.set_page_config(
    page_title="Études Structure",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🧠 Dictionnaire des pages
pages = {
    "Accueil": accueil,
    "Poutre": poutre,
    "Dalle": dalle,
    "Profilé métallique": profile_metal,
    "Tableau armatures": tableau_armatures,
    "Recouvrement": recouvrement,
    "Choix profilé": choix_profile,
    "Flambement": flambement,
    "Tableau profilés": tableau_profiles
}

# ▶️ Affichage dynamique
pages.get(st.session_state.page, accueil).show()

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

st.set_page_config(
    page_title="Études Structure",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ✅ Récupération de la page depuis les paramètres URL
if "page" in st.query_params:
    st.session_state.page = st.query_params["page"]
elif "page" not in st.session_state:
    st.session_state.page = "Accueil"

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

# ▶️ Affichage de la page sélectionnée
pages.get(st.session_state.page, accueil).show()

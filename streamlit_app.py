import streamlit as st
from modules import (
    accueil,
    poutre,
    dalle,
    corniere,
    tableau_armatures,
    age_beton,
    choix_profile,
    flambement,
    tableau_profiles,
    enrobage,
)

st.set_page_config(
    page_title="Études Structure",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ✅ Récupération de la page depuis l’URL ou session_state
if "page" in st.query_params:
    st.session_state.page = st.query_params["page"]
elif "page" not in st.session_state:
    st.session_state.page = "Accueil"

# ✅ Vérifie si un retour à l’accueil a été demandé
if st.session_state.get("retour_accueil_demande", False):
    st.session_state.page = "Accueil"
    st.session_state.retour_accueil_demande = False
    st.rerun()  # relance l’app avec la bonne page

# 🧠 Dictionnaire des pages
pages = {
    "Accueil": accueil,
    "Poutre": poutre,
    "Dalle": dalle,
    "Profilé métallique": profile_metal,
    "Tableau armatures": tableau_armatures,
    "Age béton": age_beton,
    "Cornière": corniere,
    "Flambement": flambement,
    "Tableau profilés": tableau_profiles,
    "Enrobage" : enrobage
}

# ▶️ Affichage de la page sélectionnée
pages.get(st.session_state.page, accueil).show()

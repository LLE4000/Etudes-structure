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
    initial_sidebar_state="collapsed",
)

# ✅ Récupération de la page depuis l’URL ou session_state
page_param = st.query_params.get("page") if hasattr(st, "query_params") else None
if page_param:
    st.session_state.page = page_param
elif "page" not in st.session_state:
    st.session_state.page = "Accueil"

# ✅ Retour à l’accueil demandé par une autre page ?
if st.session_state.get("retour_accueil_demande", False):
    st.session_state.page = "Accueil"
    st.session_state.retour_accueil_demande = False
    st.rerun()

# 🧠 Dictionnaire des pages -> directement les FONCTIONS show()
pages = {
    "Accueil": accueil.show,
    "Poutre": poutre.show,
    "Dalle": dalle.show,
    "Cornière": corniere.show,           # ← appellera modules/corniere.py::show()
    "Tableau armatures": tableau_armatures.show,
    "Age béton": age_beton.show,
    "Choix profilé": choix_profile.show,
    "Flambement": flambement.show,
    "Tableau profilés": tableau_profiles.show,
    "Enrobage": enrobage.show,
}

# ▶️ Affichage de la page sélectionnée
pages.get(st.session_state.page, accueil.show)()

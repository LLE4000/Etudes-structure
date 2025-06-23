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

# ✅ Initialisation sécurisée de session_state.page
if "page" not in st.session_state:
    st.session_state.page = "Accueil"

# ✅ Lecture du paramètre dans l'URL (compatibilité moderne)
query_params = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
if "page" in query_params:
    st.session_state.page = query_params["page"][0]

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

# ▶️ Affichage de la page demandée
pages.get(st.session_state.page, accueil).show()

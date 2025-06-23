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

# 🖼️ Configuration de la page
st.set_page_config(
    page_title="Études Structure",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ✅ Récupération des paramètres d'URL
query_params = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
page = query_params.get("page", [None])[0]

# ✅ Mémoriser ou mettre à jour la page
if page:
    st.session_state.page = page
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

import streamlit as st
from modules import (
    accueil,
    poutre,
    dalle,
    profile_metal,           # ✅ CORRIGÉ : anciennement `profile`
    tableau_armatures,
    recouvrement,
    choix_profile,
    flambement,
    tableau_profiles
)

# Configuration
st.set_page_config(
    page_title="Études Structure",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Page d'accueil par défaut
if "page" not in st.session_state:
    st.session_state.page = "Accueil"

# Affichage dynamique
if st.session_state.page == "Accueil":
    accueil.show()
elif st.session_state.page == "Poutre":
    poutre.show()
elif st.session_state.page == "Dalle":
    dalle.show()
elif st.session_state.page == "Profilé métallique":
    profile_metal.show()         # ✅ nom de fichier correct
elif st.session_state.page == "Tableau armatures":
    tableau_armatures.show()
elif st.session_state.page == "Recouvrement":
    recouvrement.show()
elif st.session_state.page == "Choix profilé":
    choix_profile.show()
elif st.session_state.page == "Flambement":
    flambement.show()
elif st.session_state.page == "Tableau profilés":
    tableau_profiles.show()

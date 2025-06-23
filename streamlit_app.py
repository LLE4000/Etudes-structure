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

# Configuration
st.set_page_config(
    page_title="Études Structure",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Lecture des paramètres URL
params = st.experimental_get_query_params()
page = params.get("page", ["Accueil"])[0]
st.session_state.page = page

# Navigation entre modules
if page == "Accueil":
    accueil.show()
elif page == "Poutre":
    poutre.show()
elif page == "Dalle":
    dalle.show()
elif page == "Profilé métallique":
    profile_metal.show()
elif page == "Tableau armatures":
    tableau_armatures.show()
elif page == "Recouvrement":
    recouvrement.show()
elif page == "Choix profilé":
    choix_profile.show()
elif page == "Flambement":
    flambement.show()
elif page == "Tableau profilés":
    tableau_profiles.show()

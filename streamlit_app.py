import streamlit as st
from modules import accueil, poutre, dalle, profile

# Configuration : plein écran et sidebar masquée
st.set_page_config(
    page_title="Études Structure",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Gestion de l'état de la page
if "page" not in st.session_state:
    st.session_state.page = "Accueil"

# Affichage du contenu selon la page choisie
if st.session_state.page == "Accueil":
    accueil.show()
elif st.session_state.page == "Poutre":
    poutre.show()
elif st.session_state.page == "Dalle":
    dalle.show()
elif st.session_state.page == "Profilé métallique":
    profile.show()

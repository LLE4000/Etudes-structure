import streamlit as st
from modules import poutre, dalle, profile, accueil

# Initialisation de l'état
if "page" not in st.session_state:
    st.session_state.page = "accueil"

# Barre de navigation
with st.sidebar:
    st.title("Navigation")
    if st.button("🏠 Accueil"):
        st.session_state.page = "accueil"
    if st.button("🧱 Dimensionnement Poutre"):
        st.session_state.page = "poutre"
    if st.button("🧱 Dimensionnement Dalle"):
        st.session_state.page = "dalle"
    if st.button("📐 Choix Profilé"):
        st.session_state.page = "profile"

# Affichage de la page sélectionnée
if st.session_state.page == "accueil":
    accueil.show()
elif st.session_state.page == "poutre":
    poutre.show()
elif st.session_state.page == "dalle":
    dalle.show()
elif st.session_state.page == "profile":
    profile.show()

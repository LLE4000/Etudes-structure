import streamlit as st
from modules import accueil, poutre, dalle, profile

st.set_page_config(page_title="Études Structure", page_icon="🏗️", layout="wide")

st.title("🏗️ Études Structure")

# Menu de navigation
page = st.sidebar.radio("Navigation", ["Accueil", "Poutre", "Dalle", "Profilé métallique"])

# Routing
if page == "Accueil":
    accueil.show()
elif page == "Poutre":
    poutre.show()
elif page == "Dalle":
    dalle.show()
elif page == "Profilé métallique":
    profile.show()

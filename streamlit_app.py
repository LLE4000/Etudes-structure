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

# Initialisation de la page d'accueil
if "page" not in st.session_state:
    st.session_state.page = "Accueil"

# 📡 Réception du message JS pour mise à jour de session_state
import streamlit.components.v1 as components
components.html("""
<script>
    window.addEventListener("message", (event) => {
        if (event.data.type === "streamlit:setComponentValue") {
            window.parent.postMessage({ type: "streamlit:setSessionState", page: event.data.value }, "*");
        }
    });
</script>
""", height=0)

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Études Structure",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Affichage dynamique des modules
if st.session_state.page == "Accueil":
    accueil.show()
elif st.session_state.page == "Poutre":
    poutre.show()
elif st.session_state.page == "Dalle":
    dalle.show()
elif st.session_state.page == "Profilé métallique":
    profile_metal.show()
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

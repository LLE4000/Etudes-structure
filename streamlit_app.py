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
    garde_corps,   # ⬅️ IMPORTANT : import du module
)

st.set_page_config(page_title="Études Structure", layout="wide", initial_sidebar_state="collapsed")

# ---- Récupération fiable du paramètre ?page=... (toutes versions de Streamlit)
page_param = None
try:
    qp = st.query_params                               # Streamlit récent
    page_param = qp.get("page", None)
except Exception:
    qp = st.experimental_get_query_params()            # fallback anciens
    if "page" in qp:
        v = qp["page"]
        page_param = v[0] if isinstance(v, list) else v

if page_param:
    st.session_state.page = page_param
elif "page" not in st.session_state:
    st.session_state.page = "Accueil"

# retour à l’accueil demandé ?
if st.session_state.get("retour_accueil_demande", False):
    st.session_state.page = "Accueil"
    st.session_state.retour_accueil_demande = False
    st.rerun()

# ---- Dictionnaire des pages → directement vers les FONCTIONS show()
pages = {
    "Accueil": accueil.show,
    "Poutre": poutre.show,
    "Dalle": dalle.show,
    "Cornière": corniere.show,
    "Garde-corps": garde_corps.show,   # ⬅️ IMPORTANT : clé EXACTE
    "Tableau armatures": tableau_armatures.show,
    "Age béton": age_beton.show,
    "Choix profilé": choix_profile.show,
    "Flambement": flambement.show,
    "Tableau profilés": tableau_profiles.show,
    "Enrobage": enrobage.show,
}

# ---- Affichage
pages.get(st.session_state.page, accueil.show)()

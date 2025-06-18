import streamlit as st

def show():
    # Bouton retour à l'accueil
    if st.button("🏠 Retour à l'accueil"):
        st.session_state.page = "Accueil"
        st.rerun()


def show():
    st.title("Dalle en béton armé")
    ep = st.number_input("Épaisseur (cm)", key="dalle_ep")
    portee = st.number_input("Portée (m)", key="dalle_portee")
    st.write("Épaisseur =", ep, "| Portée =", portee)

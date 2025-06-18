import streamlit as st

def show():
    st.title("Dalle en béton armé")

    ep = st.number_input("Épaisseur (cm)", key="dalle_ep")
    portee = st.number_input("Portée (m)", key="dalle_portee")

    st.write("Épaisseur =", ep, "| Portée =", portee)

    st.markdown("---")
    if st.button("⬅️ Retour à l'accueil"):
        st.session_state.page = "Accueil"
        st.experimental_rerun()


def show():
    st.title("Dalle en béton armé")
    ep = st.number_input("Épaisseur (cm)", key="dalle_ep")
    portee = st.number_input("Portée (m)", key="dalle_portee")
    st.write("Épaisseur =", ep, "| Portée =", portee)

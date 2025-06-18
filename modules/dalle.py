import streamlit as st

def show():
    st.title("Dalle en béton armé")
    ep = st.number_input("Épaisseur (cm)", key="dalle_ep")
    portee = st.number_input("Portée (m)", key="dalle_portee")
    st.write("Épaisseur =", ep, "| Portée =", portee)

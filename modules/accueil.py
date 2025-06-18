import streamlit as st

def show():
    st.markdown("<h1 style='text-align: center;'>🏗️ Études Structure</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;'>Bienvenue dans votre outil de calcul</h4>", unsafe_allow_html=True)
    st.write("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📐 Poutre en béton armé"):
            st.session_state.page = "Poutre"

    with col2:
        if st.button("🧱 Dalle en béton"):
            st.session_state.page = "Dalle"

    with col3:
        if st.button("🏗️ Profilé métallique"):
            st.session_state.page = "Profilé métallique"

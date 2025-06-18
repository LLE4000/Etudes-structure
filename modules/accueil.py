import streamlit as st

def show():
    st.markdown("<h1 style='text-align: center;'>🧱🏗️ Études Structure</h1>", unsafe_allow_html=True)
    st.markdown("### 🧱 Béton")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📐 Dimensionnement poutre"):
            st.session_state.page = "Poutre"
        if st.button("🧱 Dimensionnement dalle"):
            st.session_state.page = "Dalle"
    with col2:
        if st.button("📊 Tableau armatures"):
            st.session_state.page = "Tableau armatures"
        if st.button("📏 Longueur de recouvrement"):
            st.session_state.page = "Recouvrement"

    st.markdown("---")
    st.markdown("### 🏗️ Acier")
    col3, col4 = st.columns(2)
    with col3:
        if st.button("🏗️ Dimensionnement profilé métallique"):
            st.session_state.page = "Dimensionnement métallique"
        if st.button("🔎 Choix profilé métallique"):
            st.session_state.page = "Choix profilé"
    with col4:
        if st.button("📉 Calcul flambement"):
            st.session_state.page = "Flambement"
        if st.button("📚 Tableau profilés classiques"):
            st.session_state.page = "Tableau profilés"

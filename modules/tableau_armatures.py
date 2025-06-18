import streamlit as st

def show():
    # --- Titre et bouton Accueil aligné à droite ---
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("## 📊 Tableau des sections d’armatures")
    with col2:
        if st.button("🏠 Accueil", key="retour_accueil_armatures"):
            st.session_state.page = "Accueil"

    st.markdown("---")

    # --- Affichage de l'image du tableau ---
    st.image("Tableau armature.png", caption="Tableau des sections d’armatures en mm² et espacement fixe (cm)", use_column_width=True)

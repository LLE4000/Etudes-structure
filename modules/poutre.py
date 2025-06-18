import streamlit as st
from datetime import datetime
import json

def show():
    # Titre et bouton Accueil parfaitement alignés
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("## Poutre en béton armé")
    with col2:
        if st.button("🏠 Accueil", key="retour_accueil_poutre"):
            st.session_state.page = "Accueil"

    # Redémarre proprement après changement de page
    if st.session_state.get("page") == "Accueil":
        st.experimental_rerun()

    # Chargement de la base de données béton
    with open("beton_classes.json", "r") as f:
        beton_data = json.load(f)

    # Bouton de réinitialisation avec clé unique
    if st.button("🔄 Réinitialiser", key="reset_poutre"):
        st.rerun()

    # --- COLONNES PRINCIPALES ---
    col_gauche, col_droite = st.columns([2, 3])

    # ----------- COLONNE GAUCHE -----------
    with col_gauche:
        # 1. INFOS PROJET
        st.markdown("### Informations sur le projet")
        nom = st.text_input("", placeholder="Nom du projet", key="nom_projet")
        partie = st.text_input("", placeholder="Partie", key="partie")
        col1, col2 = st.columns(2)
        with col1:
            date = st.text_input("", placeholder="Date (jj/mm/aaaa)", value=datetime.today().strftime("%d/%m/%Y"), key="date")
        with col2:
            indice = st.text_input("", placeholder="Indice", value="0", key="indice")

        # 2. CARACTÉRISTIQUES
        st.markdown("### Caractéristiques de la poutre")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            b = st.number_input("Largeur (cm)", 10, 120, 40, key="b")
        with col2:
            h = st.number_input("Hauteur (cm)", 10, 150, 60, key="h")
        with col3:
            enrobage = st.number_input("Enrobage (cm)", 2, 10, 3, key="enrobage")
        with col4:
            beton = st.selectbox("Classe de béton", list(beton_data.keys()), index=2)
        with col5:
            fyk = st.selectbox("Qualité d'acier", ["400", "500"], index=1)

        # Données béton/acier
        fck = beton_data[beton]["fck"]
        alpha_b = beton_data[beton]["alpha_b"]
        mu_val = beton_data[beton][f"mu_a{fyk}"]
        tau_lim = round(0.5 + 0.01 * (fck - 20), 2)
        fyd = int(fyk) / 1.15
        fcd = fck / 1.5

        # 3. SOLLICITATIONS
        st.markdown("### Sollicitations")
        col1, col2 = st.columns(2)
        with col1:
            M = st.number_input("Moment inférieur M (kNm)", 0.0, step=10.0)
            m_sup = st.checkbox("Ajouter un moment supérieur")
            if m_sup:
                M_sup = st.number_input("Moment supérieur M_sup (kNm)", 0.0, step=10.0)
        with col2:
            V = st.number_input("Effort tranchant V (kN)", 0.0, step=10.0)
            v_sup = st.checkbox("Ajouter un effort tranchant réduit")
            if v_sup:
                V_lim = st.number_input("Effort tranchant réduit V_limite (kN)", 0.0, step=10.0)

    # ----------- COLONNE DROITE -----------
    with col_droite:
        st.markdown("### Dimensionnement")
        d = h - enrobage
        st.markdown(f"**Hauteur utile d = h - enrobage = {h} - {enrobage} = {d:.1f} cm**")
        st.markdown("Vérification de la hauteur utile (d ≤ 0.9·h)")

        if M > 0:
            Mu = M * 1e6
            As_req = Mu / (fyd * 10 * 0.9 * d)
            As_min = 0.0013 * b * h
            As_max = 0.04 * b * h

            st.markdown(f"Section requise A = **{As_req:.1f} mm²**")
            col1, col2, col3 = st.columns([3, 3, 4])
            with col1:
                n_barres = st.selectbox("Nb barres", list(range(1, 8)), key="n_as")
            with col2:
                diam_barres = st.selectbox("Ø (mm)", [8, 10, 12, 14, 16, 20], key="ø_as")
            with col3:
                As_choisi = 3.14 * (diam_barres / 2) ** 2 * n_barres
                st.markdown(f"Section = **{As_choisi:.0f} mm²**")

            col1, col2 = st.columns([10, 1])
            with col1:
                st.write("Vérification Aₛ entre Aₛmin et Aₛmax et ≥ Aₛ requis")
            with col2:
                st.markdown("✅" if As_min <= As_choisi <= As_max and As_choisi >= As_req else "❌")

        if V > 0:
            tau = V / (0.75 * b * h)
            st.markdown(f"τ = {tau:.2f} MPa / τ_lim = {tau_lim:.2f} MPa")
            col1, col2 = st.columns([10, 1])
            with col1:
                st.write("Vérification τ ≤ τ_lim")
            with col2:
                st.markdown("✅" if tau <= tau_lim else "❌")

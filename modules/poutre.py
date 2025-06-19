import streamlit as st
from datetime import datetime
import json
import math

def show():
    # Si on vient de demander un retour à l'accueil, on rerun ici
    if st.session_state.get("retour_accueil_demande"):
        st.session_state.page = "Accueil"
        st.session_state.retour_accueil_demande = False
        st.experimental_rerun()

    # Titre + bouton Accueil aligné à droite
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("## Poutre en béton armé")
    with col2:
        if st.button("🏠 Accueil", key="retour_accueil_poutre"):
            st.session_state.retour_accueil_demande = True
            st.experimental_rerun()

    # Chargement béton
    with open("beton_classes.json", "r") as f:
        beton_data = json.load(f)

    if st.button("🔄 Réinitialiser", key="reset_poutre"):
        st.rerun()

    # Colonnes principales
    col_gauche, col_droite = st.columns([2, 2])

    # ----------- COLONNE GAUCHE -----------
    with col_gauche:
        # Infos projet
        st.markdown("### Informations sur le projet")
        st.text_input("", placeholder="Nom du projet", key="nom_projet")
        st.text_input("", placeholder="Partie", key="partie")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("", placeholder="Date (jj/mm/aaaa)", value=datetime.today().strftime("%d/%m/%Y"), key="date")
        with col2:
            st.text_input("", placeholder="Indice", value="0", key="indice")

        # Caractéristiques
        st.markdown("### Caractéristiques de la poutre")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            b = st.number_input("Larg. (cm)", 5, 1000, 20, key="b")
        with col2:
            h = st.number_input("Haut. (cm)", 5, 1000, 35, key="h")
        with col3:
            enrobage = st.number_input("Enrob. (cm)", 1, 50, 5, key="enrobage")
        with col4:
            beton = st.selectbox("Classe de béton", list(beton_data.keys()), index=2)
        with col5:
            fyk = st.selectbox("Qualité d'acier", ["400", "500"], index=1)

        # Données matériaux
        fck = beton_data[beton]["fck"]
        alpha_b = beton_data[beton]["alpha_b"]
        mu_val = beton_data[beton][f"mu_a{fyk}"]
        tau_lim = round(0.5 + 0.01 * (fck - 20), 2)
        fyd = int(fyk) / 1.15

        # Sollicitations
        st.markdown("### Sollicitations")
        col1, col2 = st.columns(2)
        with col1:
            M = st.number_input("Moment inférieur M (kNm)", 0.0, step=10.0)
            m_sup = st.checkbox("Ajouter un moment supérieur")
            M_eff = M  # valeur par défaut
            if m_sup:
                M_sup = st.number_input("Moment supérieur M_sup (kNm)", 0.0, step=10.0)
                M_eff = max(abs(M), abs(M_sup))  # valeur utilisée pour h utile
        with col2:
            V = st.number_input("Effort tranchant V (kN)", 0.0, step=10.0)
            v_sup = st.checkbox("Ajouter un effort tranchant réduit")
            if v_sup:
                V_lim = st.number_input("Effort tranchant réduit V_limite (kN)", 0.0, step=10.0)

    # ----------- COLONNE DROITE -----------
    with col_droite:
        st.markdown("### Dimensionnement")

        # Hauteur utile requise
        d_calcule = math.sqrt((M_eff * 1e6) / (alpha_b * b * mu_val)) / 10  # cm
        st.markdown(f"**h,min :** d = {d_calcule:.1f} cm")
        col1, col2 = st.columns([10, 1])
        with col1:
            st.markdown(f"h,min + enrobage = {d_calcule + enrobage:.1f} cm ≤ h = {h} cm")
        with col2:
            st.markdown("✅" if d_calcule + enrobage <= h else "❌")

        # Armatures pour M inférieur
        d = h - enrobage
        Mu = M * 1e6
        As_req = Mu / (fyd * 0.9 * d)
        As_min = 0.0013 * b * h
        As_max = 0.04 * b * h

        st.markdown("### Armatures pour M inférieur")
        st.markdown(f"**Aₛ,min = {As_min:.0f} mm²**")
        st.markdown(f"**Aₛ,max = {As_max:.0f} mm²**")
        col1, col2, col3 = st.columns([3, 3, 4])
        with col1:
            n_barres = st.selectbox("Nb barres", list(range(1, 11)), key="n_as_inf")
        with col2:
            diam_barres = st.selectbox("Ø (mm)", [6, 8, 10, 12, 14, 16, 20], key="ø_as_inf")
        with col3:
            As_choisi = n_barres * (math.pi * (diam_barres/2)**2)
            st.markdown(f"Section choisie = **{As_choisi:.0f} mm²**")

        col1, col2 = st.columns([10, 1])
        with col1:
            st.write("Vérification Aₛ ∈ [Aₛ,min ; Aₛ,max] et ≥ Aₛ,req")
        with col2:
            ok1 = As_min <= As_choisi <= As_max and As_choisi >= As_req
            st.markdown("✅" if ok1 else "❌")

        # Armatures pour M supérieur si demandé
        if m_sup:
            st.markdown("### Armatures pour M supérieur")
            Mu_sup = M_sup * 1e6
            As_sup = Mu_sup / (fyd * 0.9 * d)

            st.markdown(f"**Aₛ,req = {As_sup:.0f} mm²**")
            col1, col2, col3 = st.columns([3, 3, 4])
            with col1:
                n_sup = st.selectbox("Nb barres", list(range(1, 11)), key="n_as_sup")
            with col2:
                d_sup = st.selectbox("Ø (mm)", [6, 8, 10, 12, 14, 16, 20], key="ø_as_sup")
            with col3:
                As_sup_choisi = n_sup * (math.pi * (d_sup / 2) ** 2)
                st.markdown(f"Section choisie = **{As_sup_choisi:.0f} mm²**")

            col1, col2 = st.columns([10, 1])
            with col1:
                st.write("Vérification Aₛ ∈ [Aₛ,min ; Aₛ,max] et ≥ Aₛ,req")
            with col2:
                ok2 = As_min <= As_sup_choisi <= As_max and As_sup_choisi >= As_sup
                st.markdown("✅" if ok2 else "❌")

        # Vérification tranchant
        if V > 0:
            tau = V * 1e3 / (0.75 * b * h)
            st.markdown(f"**τ = {tau:.2f} MPa** / **τ_lim = {tau_lim:.2f} MPa**")
            col1, col2 = st.columns([10, 1])
            with col1:
                st.write("Vérification τ ≤ τ_lim")
            with col2:
                st.markdown("✅" if tau <= tau_lim else "❌")

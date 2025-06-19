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

    # Réinitialiser
    if st.button("🔄 Réinitialiser", key="reset_poutre"):
        st.rerun()

    # Colonnes de contenu
    col_gauche, col_droite = st.columns([2, 2])

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
            b = st.number_input("Larg. (cm)", 5, 1000, 20, key="b")
        with col2:
            h = st.number_input("Haut. (cm)", 5, 1000, 35, key="h")
        with col3:
            enrobage = st.number_input("Enrob. (cm)", 1, 50, 5, key="enrobage")
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

    # Étape 1 : Hauteur utile recommandée
    d_calcule = math.sqrt(( M * 1e6) / (alpha_b * b * mu_val)) / 10  # cm
    st.markdown(f"**Hauteur utile requise :** d = {d_calcule:.1f} cm")
    col1, col2 = st.columns([10, 1])
    with col1:
        st.markdown(f"Vérification : d_calcule + enrobage = {d_calcule + enrobage/10:.1f} cm ≤ h = {h} cm")
    with col2:
        st.markdown("✅" if d_calcule + enrobage/10 <= h else "❌")

    # Étape 2 : Armatures
    d = h - enrobage  # mm
    Mu = M * 1e6
    fyd = 500 / 1.5  # N/mm²
    As_req = Mu / (fyd * 0.9 * d)  # mm²
    As_min = 0.0013 * b * h
    As_max = 0.04 * b * h

    st.markdown(f"**Armatures inférieures :** Aₛ,req = {As_req:.0f} mm²")
    col1, col2, col3 = st.columns([3, 3, 4])
    with col1:
        n_barres = st.selectbox("Nb barres", list(range(1, 11)), key="n_as")
    with col2:
        diam_barres = st.selectbox("Ø (mm)", [6, 8, 10, 12, 14, 16, 20], key="ø_as")
    with col3:
        As_choisi = n_barres * (math.pi * (diam_barres/2)**2)
        st.markdown(f"Section choisie = **{As_choisi:.0f} mm²**")

    col1, col2 = st.columns([10, 1])
    with col1:
        st.write("Vérification Aₛ ≥ Aₛ,req et Aₛ ∈ [Aₛ,min ; Aₛ,max]")
    with col2:
        ok_armature = As_min <= As_choisi <= As_max and As_choisi >= As_req
        st.markdown("✅" if ok_armature else "❌")

    # Étape 3 : Effort tranchant
    if V > 0:
        tau = V * 1e3 / (0.75 * b * h)
        st.markdown(f"**τ = {tau:.2f} MPa** / **τ_lim = {tau_lim:.2f} MPa**")
        col1, col2 = st.columns([10, 1])
        with col1:
            st.write("Vérification τ ≤ τ_lim")
        with col2:
            st.markdown("✅" if tau <= tau_lim else "❌")


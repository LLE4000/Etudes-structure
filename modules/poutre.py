import streamlit as st
from datetime import datetime
import json
import math

def show():
    if st.session_state.get("retour_accueil_demande"):
        st.session_state.page = "Accueil"
        st.session_state.retour_accueil_demande = False
        st.experimental_rerun()

    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("## Poutre en béton armé")
    with col2:
        if st.button("🏠 Accueil", key="retour_accueil_poutre"):
            st.session_state.retour_accueil_demande = True
            st.experimental_rerun()

    with open("beton_classes.json", "r") as f:
        beton_data = json.load(f)

    if st.button("🔄 Réinitialiser", key="reset_poutre"):
        st.rerun()

    col_gauche, col_droite = st.columns([2, 2])

    # --- COLONNE GAUCHE ---
    with col_gauche:
        st.markdown("### Informations sur le projet")
        st.text_input("", placeholder="Nom du projet", key="nom_projet")
        st.text_input("", placeholder="Partie", key="partie")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("", placeholder="Date (jj/mm/aaaa)", value=datetime.today().strftime("%d/%m/%Y"), key="date")
        with col2:
            st.text_input("", placeholder="Indice", value="0", key="indice")

        st.markdown("### Caractéristiques de la poutre")
        col1, col2 = st.columns(3)
        with col1:
            beton = st.selectbox("Classe de béton", list(beton_data.keys()), index=2)
        with col2:
            fyk = st.selectbox("Qualité d'acier [N/mm²]", ["400", "500"], index=1)

        col1, col2, col3 = st.columns(3)
        with col1:
            b = st.number_input("Larg. [cm]", 5, 1000, 20, key="b")
        with col2:
            h = st.number_input("Haut. [cm]", 5, 1000, 35, key="h")
        with col3:
            enrobage = st.number_input("Enrob. (cm)", 1, 100, 5, key="enrobage")

        fck = beton_data[beton]["fck"]
        fck_cube = beton_data[beton]["fck_cube"]
        alpha_b = beton_data[beton]["alpha_b"]
        mu_val = beton_data[beton][f"mu_a{fyk}"]
        fyd = int(fyk) / 1.5

        st.markdown("### Sollicitations")
        col1, col2 = st.columns(2)
        with col1:
            M_inf = st.number_input("Moment inférieur M (kNm)", 0.0, step=10.0)
            m_sup = st.checkbox("Ajouter un moment supérieur")
            M_max = M_inf
            if m_sup:
                M_sup = st.number_input("Moment supérieur M_sup (kNm)", 0.0, step=10.0)
                M_max = max(abs(M_inf), abs(M_sup))
        with col2:
            V = st.number_input("Effort tranchant V (kN)", 0.0, step=10.0)
            v_sup = st.checkbox("Ajouter un effort tranchant réduit")
            if v_sup:
                V_lim = st.number_input("Effort tranchant réduit V_limite (kN)", 0.0, step=10.0)

    # --- COLONNE DROITE ---
    with col_droite:
        st.markdown("### Dimensionnement")

        st.markdown("**Vérification de la hauteur**")
        d_calcule = math.sqrt((M_max * 1e6) / (alpha_b * b * 10 * mu_val)) / 10
        st.markdown(f"**h,min** = {d_calcule:.1f} cm")
        col1, col2 = st.columns([10, 1])
        with col1:
            st.markdown(f"h,min + enrobage = {d_calcule + enrobage:.1f} cm ≤ h = {h} cm")
        with col2:
            st.markdown("✅" if d_calcule + enrobage <= h else "❌")

        # Armatures
        d = h - enrobage
        As_inf = (M_inf * 1e6) / (fyd * 0.9 * d * 10)
        As_min = 0.0013 * b * h * 1e2
        As_max = 0.04 * b * h * 1e2

        st.markdown("**Armatures inférieures**" if not m_sup else "**Armatures inférieures (avec M_sup)**")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Aₛ,inf = {As_inf:.0f} mm²**")
        with col2:
            st.markdown(f"**Aₛ,min = {As_min:.0f} mm²**")
        with col3:
            st.markdown(f"**Aₛ,max = {As_max:.0f} mm²**")

        col1, col2, col3 = st.columns([3, 3, 4])
        with col1:
            n_barres = st.selectbox("Nb barres", list(range(1, 11)), key="n_as_inf")
        with col2:
            diam_barres = st.selectbox("Ø (mm)", [6, 8, 10, 12, 16, 20, 25, 32, 40], key="ø_as_inf")
        with col3:
            As_choisi = n_barres * (math.pi * (diam_barres / 2) ** 2)
            ok1 = As_min <= As_choisi <= As_max and As_choisi >= As_inf
            st.markdown(f"Section choisie = **{As_choisi:.0f} mm²** {'✅' if ok1 else '❌'}")

        if m_sup:
            st.markdown("**Armatures supérieures**")
            As_sup = (M_sup * 1e6) / (fyd * 0.9 * d * 10)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Aₛ,sup = {As_sup:.0f} mm²**")
            with col2:
                st.markdown(f"**Aₛ,min = {As_min:.0f} mm²**")
            with col3:
                st.markdown(f"**Aₛ,max = {As_max:.0f} mm²**")

            col1, col2, col3 = st.columns([3, 3, 4])
            with col1:
                n_sup = st.selectbox("Nb barres", list(range(1, 11)), key="n_as_sup")
            with col2:
                d_sup = st.selectbox("Ø (mm)", [6, 8, 10, 12, 16, 20, 25, 32, 40], key="ø_as_sup")
            with col3:
                As_sup_choisi = n_sup * (math.pi * (d_sup / 2) ** 2)
                ok2 = As_min <= As_sup_choisi <= As_max and As_sup_choisi >= As_sup
                st.markdown(f"Section choisie = **{As_sup_choisi:.0f} mm²** {'✅' if ok2 else '❌'}")

        # --- Vérification effort tranchant ---
        st.markdown("**Vérification de l'effort tranchant**")
        if V > 0:
            tau = V * 1e3 / (0.75 * b * h * 100)
            tau_1 = 0.016 * fck_cube / 1.05
            tau_3 = 0.064 * fck_cube / 1.05
            tau_4 = 0.096 * fck_cube / 1.05

            if tau <= tau_1:
                besoin = "Pas besoin d’étriers"
                icone = "✅"
                tau_lim_aff = tau_1
                nom_lim = "τ_adm_I"
            elif tau <= tau_3:
                besoin = "Besoin d’étriers"
                icone = "✔️"
                tau_lim_aff = tau_3
                nom_lim = "τ_adm_II"
            elif tau <= tau_4:
                besoin = "Besoin de barres inclinées et d’étriers"
                icone = "⚠️"
                tau_lim_aff = tau_4
                nom_lim = "τ_adm_III"
            else:
                besoin = "Non conforme (au-dessus de la limite)"
                icone = "❌"
                tau_lim_aff = tau_4
                nom_lim = "τ_adm_III"

            st.markdown(f"**τ = {tau:.2f} N/mm² ≤ {nom_lim} = {tau_lim_aff:.2f} N/mm² → {besoin} {icone}**")

        st.markdown("**Étriers (valeur réduite)**" if v_sup else "**Étriers**")
        if v_sup and V_lim > 0:
            tau_r = V_lim * 1e3 / (0.75 * b * h * 100)
            if tau_r <= tau_1:
                besoin_r = "Pas besoin d’étriers"
                icone_r = "✅"
                tau_lim_aff_r = tau_1
                nom_lim_r = "τ_adm_I"
            elif tau_r <= tau_3:
                besoin_r = "Besoin d’étriers"
                icone_r = "✔️"
                tau_lim_aff_r = tau_3
                nom_lim_r = "τ_adm_II"
            elif tau_r <= tau_4:
                besoin_r = "Besoin de barres inclinées et d’étriers"
                icone_r = "⚠️"
                tau_lim_aff_r = tau_4
                nom_lim_r = "τ_adm_III"
            else:
                besoin_r = "Non conforme (au-dessus de la limite)"
                icone_r = "❌"
                tau_lim_aff_r = tau_4
                nom_lim_r = "τ_adm_III"

            st.markdown(f"**τ = {tau_r:.2f} N/mm² ≤ {nom_lim_r} = {tau_lim_aff_r:.2f} N/mm² → {besoin_r} {icone_r}**")
            st.markdown("_En construction : calcul de la section d’étriers avec V réduit._")
        elif not v_sup:
            st.markdown("_En construction : calcul de la section d’étriers selon effort tranchant standard._")

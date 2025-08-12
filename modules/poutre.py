import streamlit as st
from datetime import datetime
import json
import math
import base64


# ========= Utilitaires UI =========

C_COULEURS = {
    "ok":   "#e6ffe6",  # vert pâle
    "warn": "#fffbe6",  # jaune pâle
    "nok":  "#ffe6e6",  # rouge pâle
}
C_ICONES = {
    "ok":   "✅",
    "warn": "⚠️",
    "nok":  "❌",
}

def open_bloc(titre: str, etat: str = "ok"):
    """
    Ouvre un bloc visuel (fond coloré + bord + header) et laisse le <div> ouvert.
    Appeler ensuite close_bloc() pour fermer le <div>.
    """
    st.markdown(
        f"""
        <div style="
            background-color:{C_COULEURS.get(etat, '#f6f6f6')};
            padding:12px 14px 10px 14px;
            border-radius:10px;
            border:1px solid #d9d9d9;
            margin:10px 0 12px 0;
        ">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:6px;">
            <div style="font-weight:700;">{titre}</div>
            <div style="font-size:20px;line-height:1;">{C_ICONES.get(etat,'')}</div>
          </div>
        """,
        unsafe_allow_html=True
    )

def close_bloc():
    st.markdown("</div>", unsafe_allow_html=True)


def show():
    # ---------- État ----------
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    if "retour_accueil_demande" not in st.session_state:
        st.session_state.retour_accueil_demande = False

    if st.session_state.retour_accueil_demande:
        st.session_state.page = "Accueil"
        st.session_state.retour_accueil_demande = False
        st.rerun()

    st.markdown("## Poutre en béton armé")

    # ---------- Barre d’actions ----------
    btn1, btn2, btn3, btn4, btn5 = st.columns(5)

    with btn1:
        if st.button("🏠 Accueil", use_container_width=True, key="btn_accueil"):
            st.session_state.retour_accueil_demande = True
            st.rerun()

    with btn2:
        if st.button("🔄 Réinitialiser", use_container_width=True, key="btn_reset"):
            st.rerun()

    with btn3:
        if st.button("💾 Enregistrer", use_container_width=True, key="btn_save"):
            dict_a_sauver = {
                k: v for k, v in st.session_state.items()
                if isinstance(v, (int, float, str, bool, list, dict, type(None)))
            }
            contenu_json = json.dumps(dict_a_sauver, indent=2)
            b64 = base64.b64encode(contenu_json.encode()).decode()
            href = f'<a href="data:application/json;base64,{b64}" download="sauvegarde.json">📥 Télécharger</a>'
            st.markdown(href, unsafe_allow_html=True)

    with btn4:
        if "ouvrir_fichier" not in st.session_state:
            st.session_state.ouvrir_fichier = False

        if st.button("📂 Ouvrir", use_container_width=True, key="btn_open_trigger"):
            st.session_state.ouvrir_fichier = True
            st.rerun()

        if st.session_state.ouvrir_fichier:
            uploaded = st.file_uploader("Choisir un fichier JSON", type=["json"], label_visibility="collapsed", key="btn_open_uploader")
            if uploaded is not None:
                contenu = json.load(uploaded)
                for k, v in contenu.items():
                    st.session_state[k] = v
                st.session_state.ouvrir_fichier = False
                st.rerun()

    with btn5:
        if st.button("📄 Générer PDF", use_container_width=True, key="btn_pdf"):
            from modules.export_pdf import generer_rapport_pdf
            fichier_pdf = generer_rapport_pdf(
                nom_projet=st.session_state.get("nom_projet", ""),
                partie=st.session_state.get("partie", ""),
                date=st.session_state.get("date", ""),
                indice=st.session_state.get("indice", ""),
                beton=st.session_state.get("beton", ""),
                fyk=st.session_state.get("fyk", ""),
                b=st.session_state.get("b", 0),
                h=st.session_state.get("h", 0),
                enrobage=st.session_state.get("enrobage", 0),
                M_inf=st.session_state.get("M_inf", 0),
                M_sup=st.session_state.get("M_sup", 0),
                V=st.session_state.get("V", 0),
                V_lim=st.session_state.get("V_lim", 0),  # clé interne conservée
            )
            with open(fichier_pdf, "rb") as f:
                st.download_button(
                    label="⬇️ Télécharger le rapport PDF",
                    data=f,
                    file_name=fichier_pdf,
                    mime="application/pdf",
                    key="btn_pdf_dl"
                )
            st.success("✅ Rapport généré")

    # ---------- Données béton ----------
    with open("beton_classes.json", "r") as f:
        beton_data = json.load(f)

    input_col_gauche, result_col_droite = st.columns([2, 3])

    # ---------- COLONNE GAUCHE ----------
    with input_col_gauche:
        st.markdown("### Informations sur le projet")
        afficher_infos = st.checkbox("Ajouter les informations du projet", value=False, key="show_infos_projet")
        if afficher_infos:
            st.text_input("", placeholder="Nom du projet", key="nom_projet")
            st.text_input("", placeholder="Partie", key="partie")
            date_col, indice_col = st.columns(2)
            with date_col:
                st.text_input("", placeholder="Date (jj/mm/aaaa)",
                              value=datetime.today().strftime("%d/%m/%Y"), key="date")
            with indice_col:
                st.text_input("", placeholder="Indice", value="0", key="indice")
        else:
            st.session_state.setdefault("date", datetime.today().strftime("%d/%m/%Y"))

        st.markdown("### Caractéristiques de la poutre")
        beton_col, acier_col = st.columns(2)
        with beton_col:
            beton = st.selectbox("Classe de béton", list(beton_data.keys()),
                                 index=min(2, len(beton_data) - 1), key="beton")
        with acier_col:
            fyk = st.selectbox("Qualité d'acier [N/mm²]", ["400", "500"], index=1, key="fyk")

        section_col1, section_col2, section_col3 = st.columns(3)
        with section_col1:
            b = st.number_input("Larg. [cm]", min_value=5, max_value=1000, value=20, step=5, key="b")
        with section_col2:
            h = st.number_input("Haut. [cm]", min_value=5, max_value=1000, value=40, step=5, key="h")
        with section_col3:
            enrobage = st.number_input("Enrob. (cm)", min_value=0.0, max_value=100.0, value=5.0, step=0.5, key="enrobage")

        # Constantes matériau
        fck = beton_data[beton]["fck"]
        fck_cube = beton_data[beton]["fck_cube"]
        alpha_b = beton_data[beton]["alpha_b"]
        mu_val = beton_data[beton][f"mu_a{fyk}"]
        fyd = int(fyk) / 1.5

        st.markdown("### Sollicitations")
        moment_col, effort_col = st.columns(2)

        with moment_col:
            M_inf = st.number_input("Moment inférieur M (kNm)", 0.0, step=10.0, key="M_inf")
            m_sup = st.checkbox("Ajouter un moment supérieur", key="ajouter_moment_sup")
            if m_sup:
                M_sup = st.number_input("Moment supérieur M_sup (kNm)", 0.0, step=10.0, key="M_sup")
            else:
                M_sup = 0.0

        with effort_col:
            V = st.number_input("Effort tranchant V (kN)", 0.0, step=10.0, key="V")
            v_sup = st.checkbox("Ajouter un effort tranchant réduit", key="ajouter_effort_reduit")
            if v_sup:
                V_lim = st.number_input("Effort tranchant réduit V_réduit (kN)", 0.0, step=10.0, key="V_lim")
            else:
                V_lim = 0.0
                if "V_lim" in st.session_state:
                    del st.session_state["V_lim"]

        # Nettoyage résiduel
        if not m_sup and "M_sup" in st.session_state:
            del st.session_state["M_sup"]

    # ---------- COLONNE DROITE ----------
    with result_col_droite:
        st.markdown("### Dimensionnement")

        # ---- Vérification de la hauteur ----
        M_max = max(M_inf, M_sup)
        d_calcule = math.sqrt((M_max * 1e6) / (alpha_b * b * 10 * mu_val)) / 10  # cm
        etat_hauteur = "ok" if d_calcule + enrobage <= h else "nok"
        open_bloc("Vérification de la hauteur", etat_hauteur)
        st.markdown(
            f"**h,min** = {d_calcule:.1f} cm  \n"
            f"h,min + enrobage = {d_calcule + enrobage:.1f} cm ≤ h = {h} cm"
        )
        close_bloc()

        # Données section
        d_utile = h - enrobage  # cm
        As_min = 0.0013 * b * h * 1e2
        As_max = 0.04 * b * h * 1e2

        # ---- Armatures inférieures ----
        As_inf = (M_inf * 1e6) / (fyd * 0.9 * d_utile * 10)
        As_inf_bloc_ok = False  # sera mis à jour après saisies
        open_bloc("Armatures inférieures", "ok")  # état ajusté après calcul
        col_ai1, col_ai2, col_ai3 = st.columns(3)
        with col_ai1:
            st.markdown(f"**Aₛ,inf = {As_inf:.0f} mm²**")
        with col_ai2:
            st.markdown(f"**Aₛ,min = {As_min:.0f} mm²**")
        with col_ai3:
            st.markdown(f"**Aₛ,max = {As_max:.0f} mm²**")

        c1, c2, c3 = st.columns([3, 3, 4])
        with c1:
            n_barres = st.number_input("Nb barres", min_value=1, max_value=50, value=2, step=1, key="n_as_inf")
        with c2:
            diam_barres = st.selectbox("Ø (mm)", [6, 8, 10, 12, 16, 20, 25, 32, 40], index=4, key="ø_as_inf")
        with c3:
            As_choisi = n_barres * (math.pi * (diam_barres / 2) ** 2)
            As_inf_bloc_ok = (As_min <= As_choisi <= As_max) and (As_choisi >= As_inf)
            st.markdown(f"Section choisie = **{As_choisi:.0f} mm²**")
        close_bloc()
        # mettre à jour visuel du bandeau (simple: si NOK, on réaffiche la bordure en rouge)
        if not As_inf_bloc_ok:
            open_bloc("Armatures inférieures", "nok")
            st.markdown("**Section non conforme.**")
            close_bloc()

        # ---- Armatures supérieures (si M_sup) ----
        if m_sup:
            As_sup = (M_sup * 1e6) / (fyd * 0.9 * d_utile * 10)
            As_sup_bloc_ok = False
            open_bloc("Armatures supérieures", "ok")
            col_as1, col_as2, col_as3 = st.columns(3)
            with col_as1:
                st.markdown(f"**Aₛ,sup = {As_sup:.0f} mm²**")
            with col_as2:
                st.markdown(f"**Aₛ,min = {As_min:.0f} mm²**")
            with col_as3:
                st.markdown(f"**Aₛ,max = {As_max:.0f} mm²**")

            cs1, cs2, cs3 = st.columns([3, 3, 4])
            with cs1:
                n_sup = st.number_input("Nb barres (sup.)", min_value=1, max_value=50, value=2, step=1, key="n_as_sup")
            with cs2:
                d_sup = st.selectbox("Ø (mm) (sup.)", [6, 8, 10, 12, 16, 20, 25, 32, 40], index=4, key="ø_as_sup")
            with cs3:
                As_sup_choisi = n_sup * (math.pi * (d_sup / 2) ** 2)
                As_sup_bloc_ok = (As_min <= As_sup_choisi <= As_max) and (As_sup_choisi >= As_sup)
                st.markdown(f"Section choisie = **{As_sup_choisi:.0f} mm²**")
            close_bloc()
            if not As_sup_bloc_ok:
                open_bloc("Armatures supérieures", "nok")
                st.markdown("**Section non conforme.**")
                close_bloc()

        # ---- Effort tranchant (standard) ----
        tau_1 = 0.016 * fck_cube / 1.05
        tau_2 = 0.032 * fck_cube / 1.05
        tau_4 = 0.064 * fck_cube / 1.05

        if V > 0:
            tau = V * 1e3 / (0.75 * b * h * 100)

            if tau <= tau_1:
                besoin, etat_tau = "Pas besoin d’étriers", "ok"
                tau_lim_aff, nom_lim = tau_1, "τ_adm_I"
            elif tau <= tau_2:
                besoin, etat_tau = "Besoin d’étriers", "ok"
                tau_lim_aff, nom_lim = tau_2, "τ_adm_II"
            elif tau <= tau_4:
                besoin, etat_tau = "Besoin de barres inclinées et d’étriers", "warn"
                tau_lim_aff, nom_lim = tau_4, "τ_adm_IV"
            else:
                besoin, etat_tau = "Pas acceptable", "nok"
                tau_lim_aff, nom_lim = tau_4, "τ_adm_IV"

            open_bloc("Vérification de l'effort tranchant", etat_tau)
            st.markdown(f"τ = {tau:.2f} N/mm² ≤ {nom_lim} = {tau_lim_aff:.2f} N/mm² → {besoin}")
            close_bloc()

            # Détermination des étriers
            open_bloc("Détermination des étriers", "ok")
            col1, col2, col3 = st.columns(3)
            with col1:
                n_etriers = st.number_input("Nbr. étriers", min_value=1, max_value=8, value=1, step=1, key="n_etriers")
            with col2:
                d_etrier = st.selectbox("Ø étriers (mm)", [6, 8, 10, 12], key="ø_etrier")
            with col3:
                pas_choisi = st.number_input("Pas choisi (cm)", min_value=5.0, max_value=50.0, value=5.0,
                                             step=0.5, key="pas_etrier")

            Ast_etrier = n_etriers * math.pi * (d_etrier / 2) ** 2
            pas_theorique = Ast_etrier * fyd * d_utile * 10 / (10 * V * 1e3)

            if pas_choisi <= pas_theorique:
                etat_pas = "ok"
            elif pas_choisi <= 30:
                etat_pas = "warn"
            else:
                etat_pas = "nok"

            st.markdown(
                f"**Pas théorique = {pas_theorique:.1f} cm — Pas choisi = {pas_choisi:.1f} cm**"
            )
            close_bloc()
            # bandeau d’état du pas (affichage synthèse)
            if etat_pas != "ok":
                open_bloc("Détermination des étriers — synthèse", etat_pas)
                st.markdown("Ajuster le pas choisi ou la géométrie des étriers.")
                close_bloc()

        # ---- Effort tranchant réduit (si activé) ----
        if v_sup and V_lim > 0:
            tau_r = V_lim * 1e3 / (0.75 * b * h * 100)

            if tau_r <= tau_1:
                besoin_r, etat_r = "Pas besoin d’étriers", "ok"
                tau_lim_aff_r, nom_lim_r = tau_1, "τ_adm_I"
            elif tau_r <= tau_2:
                besoin_r, etat_r = "Besoin d’étriers", "ok"
                tau_lim_aff_r, nom_lim_r = tau_2, "τ_adm_II"
            elif tau_r <= tau_4:
                besoin_r, etat_r = "Besoin de barres inclinées et d’étriers", "warn"
                tau_lim_aff_r, nom_lim_r = tau_4, "τ_adm_IV"
            else:
                besoin_r, etat_r = "Pas acceptable", "nok"
                tau_lim_aff_r, nom_lim_r = tau_4, "τ_adm_IV"

            open_bloc("Vérification de l'effort tranchant réduit", etat_r)
            st.markdown(f"τ = {tau_r:.2f} N/mm² ≤ {nom_lim_r} = {tau_lim_aff_r:.2f} N/mm² → {besoin_r}")
            close_bloc()

            open_bloc("Détermination des étriers réduits", "ok")
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                n_etriers_r = st.number_input("Nbr. étriers (réduit)", min_value=1, max_value=8, value=1, step=1, key="n_etriers_r")
            with col_r2:
                d_etrier_r = st.selectbox("Ø étriers (mm) (réduit)", [6, 8, 10, 12], key="ø_etrier_r")
            with col_r3:
                pas_choisi_r = st.number_input("Pas choisi (cm) (réduit)", min_value=5.0, max_value=50.0, value=5.0,
                                               step=0.5, key="pas_etrier_r")

            Ast_etrier_r = n_etriers_r * math.pi * (d_etrier_r / 2) ** 2
            pas_theorique_r = Ast_etrier_r * fyd * d_utile * 10 / (10 * V_lim * 1e3)

            if pas_choisi_r <= pas_theorique_r:
                etat_pas_r = "ok"
            elif pas_choisi_r <= 30:
                etat_pas_r = "warn"
            else:
                etat_pas_r = "nok"

            st.markdown(
                f"**Pas théorique = {pas_theorique_r:.1f} cm — Pas choisi = {pas_choisi_r:.1f} cm**"
            )
            close_bloc()
            if etat_pas_r != "ok":
                open_bloc("Détermination des étriers réduits — synthèse", etat_pas_r)
                st.markdown("Ajuster le pas choisi ou la géométrie des étriers.")
                close_bloc()

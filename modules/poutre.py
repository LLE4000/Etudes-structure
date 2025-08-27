import streamlit as st
from datetime import datetime
import json
import math
import base64  # (inutile avec le nouveau save mais je laisse si tu l'utilises ailleurs)

# ========= Styles blocs =========
C_COULEURS = {"ok": "#e6ffe6", "warn": "#fffbe6", "nok": "#ffe6e6"}
C_ICONES   = {"ok": "✅",       "warn": "⚠️",      "nok": "❌"}

def open_bloc(titre: str, etat: str = "ok"):
    st.markdown(
        f"""
        <div style="
            background-color:{C_COULEURS.get(etat,'#f6f6f6')};
            padding:12px 14px 10px 14px;
            border-radius:10px;
            border:1px solid #d9d9d9;
            margin:10px 0 12px 0;">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:6px;">
            <div style="font-weight:700;">{titre}</div>
            <div style="font-size:20px;line-height:1;">{C_ICONES.get(etat,'')}</div>
          </div>
        """,
        unsafe_allow_html=True
    )

def close_bloc():
    st.markdown("</div>", unsafe_allow_html=True)


# ---------- util : vrai reset ----------
def _reset_module():
    current_page = st.session_state.get("page")
    st.session_state.clear()
    if current_page:
        st.session_state.page = current_page
    st.rerun()


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
        if st.button("🏠 Accueil", use_container_width=True, key="btn_home"):
            st.session_state.retour_accueil_demande = True
            st.rerun()

    with btn2:
        if st.button("🔄 Réinitialiser", use_container_width=True, key="btn_reset"):
            _reset_module()

    with btn3:
        # Enregistrer = téléchargement direct de l'état courant
        payload = {
            k: v for k, v in st.session_state.items()
            if isinstance(v, (int, float, str, bool, list, dict, type(None)))
        }
        st.download_button(
            label="💾 Enregistrer",
            data=json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8"),
            file_name="poutre_ba.json",
            mime="application/json",
            use_container_width=True,
            key="btn_save_dl"
        )

    with btn4:
        # Ouvrir = toggle + uploader ; charge le JSON et remplace l'état
        if st.button("📂 Ouvrir", use_container_width=True, key="btn_open_toggle"):
            st.session_state["show_open_uploader"] = not st.session_state.get("show_open_uploader", False)

        if st.session_state.get("show_open_uploader", False):
            uploaded = st.file_uploader("Choisir un fichier JSON", type=["json"], label_visibility="collapsed", key="open_uploader")
            if uploaded is not None:
                data = json.load(uploaded)
                current_page = st.session_state.get("page")
                st.session_state.clear()
                st.session_state.update(data)
                if current_page:
                    st.session_state.page = current_page
                st.session_state["show_open_uploader"] = False
                st.success("Fichier chargé.")
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
                V_lim=st.session_state.get("V_lim", 0),
            )
            with open(fichier_pdf, "rb") as f:
                st.download_button(
                    label="⬇️ Télécharger le rapport PDF",
                    data=f,
                    file_name=fichier_pdf,
                    mime="application/pdf",
                    use_container_width=True,
                )
            st.success("✅ Rapport généré")

    # ---------- Données béton ----------
    with open("beton_classes.json", "r") as f:
        beton_data = json.load(f)

    input_col_gauche, result_col_droite = st.columns([2, 3])

    # ---------- COLONNE GAUCHE ----------
    with input_col_gauche:
        st.markdown("### Informations sur le projet")
        afficher_infos = st.checkbox("Ajouter les informations du projet", value=False)
        if afficher_infos:
            st.text_input("", placeholder="Nom du projet", key="nom_projet")
            st.text_input("", placeholder="Partie", key="partie")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("", placeholder="Date (jj/mm/aaaa)",
                              value=datetime.today().strftime("%d/%m/%Y"), key="date")
            with c2:
                st.text_input("", placeholder="Indice", value="0", key="indice")
        else:
            st.session_state.setdefault("date", datetime.today().strftime("%d/%m/%Y"))

        st.markdown("### Caractéristiques de la poutre")
        cbet, cacier = st.columns(2)
        with cbet:
            beton = st.selectbox("Classe de béton", list(beton_data.keys()),
                                 index=min(2, len(beton_data)-1), key="beton")
        with cacier:
            fyk = st.selectbox("Qualité d'acier [N/mm²]", ["400", "500"], index=1, key="fyk")

        csec1, csec2, csec3 = st.columns(3)
        with csec1:
            b = st.number_input("Larg. [cm]", min_value=5, max_value=1000, value=20, step=5, key="b")
        with csec2:
            h = st.number_input("Haut. [cm]", min_value=5, max_value=1000, value=40, step=5, key="h")
        with csec3:
            enrobage = st.number_input("Enrob. (cm)", min_value=0.0, max_value=100.0, value=5.0, step=0.5, key="enrobage")

        # Matériaux
        fck       = beton_data[beton]["fck"]
        fck_cube  = beton_data[beton]["fck_cube"]
        alpha_b   = beton_data[beton]["alpha_b"]
        mu_val    = beton_data[beton][f"mu_a{fyk}"]
        fyd       = int(fyk) / 1.5

        st.markdown("### Sollicitations")
        cmom, cev  = st.columns(2)
        with cmom:
            # <- décimales fluides
            M_inf = st.number_input("Moment inférieur M (kNm)", min_value=0.0, value=0.0,
                                    step=0.01, format="%.2f", key="M_inf")
            m_sup = st.checkbox("Ajouter un moment supérieur", key="ajouter_moment_sup")
            if m_sup:
                M_sup = st.number_input("Moment supérieur M_sup (kNm)", min_value=0.0, value=0.0,
                                        step=0.01, format="%.2f", key="M_sup")
            else:
                M_sup = 0.0
                if "M_sup" in st.session_state:
                    del st.session_state["M_sup"]
        with cev:
            V = st.number_input("Effort tranchant V (kN)", min_value=0.0, value=0.0,
                                step=0.01, format="%.2f", key="V")
            v_sup = st.checkbox("Ajouter un effort tranchant réduit", key="ajouter_effort_reduit")
            if v_sup:
                V_lim = st.number_input("Effort tranchant réduit V_réduit (kN)", min_value=0.0, value=0.0,
                                        step=0.01, format="%.2f", key="V_lim")
            else:
                V_lim = 0.0
                if "V_lim" in st.session_state:
                    del st.session_state["V_lim"]

    # ---------- COLONNE DROITE ----------
    with result_col_droite:
        st.markdown("### Dimensionnement")

        # ---- Vérification de la hauteur ----
        M_max      = max(M_inf, M_sup)
        hmin_calc  = math.sqrt((M_max * 1e6) / (alpha_b * b * 10 * mu_val)) / 10  # cm
        etat_h     = "ok" if hmin_calc + enrobage <= h else "nok"
        open_bloc("Vérification de la hauteur", etat_h)
        st.markdown(f"**h,min** = {hmin_calc:.1f} cm  \n"
                    f"h,min + enrobage = {hmin_calc + enrobage:.1f} cm ≤ h = {h} cm")
        close_bloc()

        # ---- Données section (communes) ----
        d_utile = h - enrobage  # cm
        As_min  = 0.0013 * b * h * 1e2
        As_max  = 0.04   * b * h * 1e2

        # --- Armatures inférieures ---
        As_inf = (M_inf * 1e6) / (fyd * 0.9 * d_utile * 10)
        diam_opts = [6, 8, 10, 12, 16, 20, 25, 32, 40]
        n_inf_cur = st.session_state.get("n_as_inf", 2)
        diam_inf_cur = st.session_state.get("ø_as_inf", 16)
        As_inf_choisi = n_inf_cur * (math.pi * (diam_inf_cur/2)**2)
        ok_inf = (As_min <= As_inf_choisi <= As_max) and (As_inf_choisi >= As_inf)
        etat_inf = "ok" if ok_inf else "nok"
        
        open_bloc("Armatures inférieures", etat_inf)
        ca1, ca2, ca3 = st.columns(3)
        with ca1: st.markdown(f"**Aₛ,inf = {As_inf:.0f} mm²**")
        with ca2: st.markdown(f"**Aₛ,min = {As_min:.0f} mm²**")
        with ca3: st.markdown(f"**Aₛ,max = {As_max:.0f} mm²**")
        
        row1_c1, row1_c2, row1_c3 = st.columns([3, 3, 2])
        with row1_c1:
            st.number_input("Nb barres", min_value=1, max_value=50,
                            value=n_inf_cur, step=1, key="n_as_inf")
        with row1_c2:
            st.selectbox("Ø (mm)", diam_opts,
                         index=diam_opts.index(diam_inf_cur), key="ø_as_inf")
        # valeur recalculée après widgets
        n_val = st.session_state.get("n_as_inf", n_inf_cur)
        d_val = st.session_state.get("ø_as_inf", diam_inf_cur)
        As_inf_choisi = n_val * (math.pi * (d_val/2)**2)
        with row1_c3:
            st.markdown(
                f"<div style='margin-top:30px;font-weight:600;white-space:nowrap;'>( {As_inf_choisi:.0f} mm² )</div>",
                unsafe_allow_html=True
        )
        close_bloc()

        # ---- Armatures supérieures (si M_sup) : bloc unique ----
        if m_sup:
            As_sup = (M_sup * 1e6) / (fyd * 0.9 * d_utile * 10)
            n_sup_cur = st.session_state.get("n_as_sup", 2)
            diam_sup_cur = st.session_state.get("ø_as_sup", 16)
            As_sup_choisi = n_sup_cur * (math.pi * (diam_sup_cur/2)**2)
            ok_sup = (As_min <= As_sup_choisi <= As_max) and (As_sup_choisi >= As_sup)
            etat_sup = "ok" if ok_sup else "nok"
        
            open_bloc("Armatures supérieures", etat_sup)
            cs1, cs2, cs3 = st.columns(3)
            with cs1: st.markdown(f"**Aₛ,sup = {As_sup:.0f} mm²**")
            with cs2: st.markdown(f"**Aₛ,min = {As_min:.0f} mm²**")
            with cs3: st.markdown(f"**Aₛ,max = {As_max:.0f} mm²**")
        
            row2_c1, row2_c2, row2_c3 = st.columns([3, 3, 2])
            with row2_c1:
                st.number_input("Nb barres (sup.)", min_value=1, max_value=50,
                                value=n_sup_cur, step=1, key="n_as_sup")
            with row2_c2:
                st.selectbox("Ø (mm) (sup.)", diam_opts,
                             index=diam_opts.index(diam_sup_cur), key="ø_as_sup")
            # recalcul après widgets
            n_s = st.session_state.get("n_as_sup", n_sup_cur)
            d_s = st.session_state.get("ø_as_sup", diam_sup_cur)
            As_sup_choisi = n_s * (math.pi * (d_s/2)**2)
            with row2_c3:
                st.markdown(
                    f"<div style='margin-top:30px;font-weight:600;white-space:nowrap;'>( {As_sup_choisi:.0f} mm² )</div>",
                    unsafe_allow_html=True
                )
            close_bloc()

        # ---- Vérification effort tranchant ----
        tau_1 = 0.016 * fck_cube / 1.05
        tau_2 = 0.032 * fck_cube / 1.05
        tau_4 = 0.064 * fck_cube / 1.05

        if V > 0:
            tau = V * 1e3 / (0.75 * b * h * 100)
            if   tau <= tau_1: besoin, etat_tau, nom_lim, tau_lim = "Pas besoin d’étriers", "ok",  "τ_adm_I", tau_1
            elif tau <= tau_2: besoin, etat_tau, nom_lim, tau_lim = "Besoin d’étriers",      "ok",  "τ_adm_II", tau_2
            elif tau <= tau_4: besoin, etat_tau, nom_lim, tau_lim = "Besoin de barres inclinées et d’étriers", "warn", "τ_adm_IV", tau_4
            else:              besoin, etat_tau, nom_lim, tau_lim = "Pas acceptable",        "nok", "τ_adm_IV", tau_4

            open_bloc("Vérification de l'effort tranchant", etat_tau)
            st.markdown(f"τ = {tau:.2f} N/mm² ≤ {nom_lim} = {tau_lim:.2f} N/mm² → {besoin}")
            close_bloc()

            # ---- Détermination des étriers : bloc unique (couleur = état du pas) ----
            n_etriers_cur = st.session_state.get("n_etriers", 1)
            d_etrier_cur  = st.session_state.get("ø_etrier", 6)
            pas_cur       = st.session_state.get("pas_etrier", 5.0)

            Ast_e   = n_etriers_cur * math.pi * (d_etrier_cur/2)**2
            pas_th  = Ast_e * fyd * d_utile * 10 / (10 * V * 1e3)
            if   pas_cur <= pas_th: etat_pas = "ok"
            elif pas_cur <= 30:     etat_pas = "warn"
            else:                   etat_pas = "nok"

            open_bloc("Détermination des étriers", etat_pas)
            ce1, ce2, ce3 = st.columns(3)
            with ce1:
                st.number_input("Nbr. étriers", min_value=1, max_value=8, value=n_etriers_cur, step=1, key="n_etriers")
            with ce2:
                st.selectbox("Ø étriers (mm)", [6, 8, 10, 12], index=[6,8,10,12].index(d_etrier_cur), key="ø_etrier")
            with ce3:
                st.number_input("Pas choisi (cm)", min_value=5.0, max_value=50.0, value=pas_cur, step=0.5, key="pas_etrier")
            # ligne synthèse
            pas_cur = st.session_state.get("pas_etrier", pas_cur)
            d_etrier_cur = st.session_state.get("ø_etrier", d_etrier_cur)
            n_etriers_cur = st.session_state.get("n_etriers", n_etriers_cur)
            Ast_e  = n_etriers_cur * math.pi * (d_etrier_cur/2)**2
            pas_th = Ast_e * fyd * d_utile * 10 / (10 * V * 1e3)
            st.markdown(f"**Pas théorique = {pas_th:.1f} cm — Pas choisi = {pas_cur:.1f} cm**")
            close_bloc()

        # ---- Vérification effort tranchant réduit ----
        if v_sup and V_lim > 0:
            tau_r = V_lim * 1e3 / (0.75 * b * h * 100)
            if   tau_r <= tau_1: besoin_r, etat_r, nom_lim_r, tau_lim_r = "Pas besoin d’étriers", "ok",  "τ_adm_I", tau_1
            elif tau_r <= tau_2: besoin_r, etat_r, nom_lim_r, tau_lim_r = "Besoin d’étriers",     "ok",  "τ_adm_II", tau_2
            elif tau_r <= tau_4: besoin_r, etat_r, nom_lim_r, tau_lim_r = "Besoin de barres inclinées et d’étriers", "warn", "τ_adm_IV", tau_4
            else:                 besoin_r, etat_r, nom_lim_r, tau_lim_r = "Pas acceptable",       "nok", "τ_adm_IV", tau_4

            open_bloc("Vérification de l'effort tranchant réduit", etat_r)
            st.markdown(f"τ = {tau_r:.2f} N/mm² ≤ {nom_lim_r} = {tau_lim_r:.2f} N/mm² → {besoin_r}")
            close_bloc()

            # Détermination des étriers réduits : bloc unique
            n_et_r_cur = st.session_state.get("n_etriers_r", 1)
            d_et_r_cur = st.session_state.get("ø_etrier_r", 6)
            pas_r_cur  = st.session_state.get("pas_etrier_r", 5.0)

            Ast_er  = n_et_r_cur * math.pi * (d_et_r_cur/2)**2
            pas_th_r = Ast_er * fyd * d_utile * 10 / (10 * V_lim * 1e3)
            if   pas_r_cur <= pas_th_r: etat_pas_r = "ok"
            elif pas_r_cur <= 30:       etat_pas_r = "warn"
            else:                       etat_pas_r = "nok"

            open_bloc("Détermination des étriers réduits", etat_pas_r)
            cr1, cr2, cr3 = st.columns(3)
            with cr1:
                st.number_input("Nbr. étriers (réduit)", min_value=1, max_value=8, value=n_et_r_cur, step=1, key="n_etriers_r")
            with cr2:
                st.selectbox("Ø étriers (mm) (réduit)", [6, 8, 10, 12], index=[6,8,10,12].index(d_et_r_cur), key="ø_etrier_r")
            with cr3:
                st.number_input("Pas choisi (cm) (réduit)", min_value=5.0, max_value=50.0, value=pas_r_cur, step=0.5, key="pas_etrier_r")
            # ligne synthèse
            n_et_r_cur = st.session_state.get("n_etriers_r", n_et_r_cur)
            d_et_r_cur = st.session_state.get("ø_etrier_r", d_et_r_cur)
            pas_r_cur  = st.session_state.get("pas_etrier_r", pas_r_cur)
            Ast_er   = n_et_r_cur * math.pi * (d_et_r_cur/2)**2
            pas_th_r = Ast_er * fyd * d_utile * 10 / (10 * V_lim * 1e3)
            st.markdown(f"**Pas théorique = {pas_th_r:.1f} cm — Pas choisi = {pas_r_cur:.1f} cm**")
            close_bloc()

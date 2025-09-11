import streamlit as st
from datetime import datetime
import json
import math
import importlib  # <— ajouté

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

# ========= Clés à sauvegarder/charger (métier uniquement) =========
SAVE_KEYS = {
    # infos projet
    "nom_projet", "partie", "date", "indice",
    # matériaux / géométrie
    "beton", "fyk", "b", "h", "enrobage",
    # sollicitations
    "M_inf", "ajouter_moment_sup", "M_sup",
    "V", "ajouter_effort_reduit", "V_lim",
    # armatures
    "n_as_inf", "ø_as_inf", "n_as_sup", "ø_as_sup",
    # étriers
    "n_etriers", "ø_etrier", "pas_etrier",
    "n_etriers_r", "ø_etrier_r", "pas_etrier_r",
}

# ========= Réinitialisation propre =========
def _reset_module():
    current_page = st.session_state.get("page")
    st.session_state.clear()
    if current_page:
        st.session_state.page = current_page
    st.rerun()

# ========= Saisie décimale FR (texte seul, pas de −/+) =========
def float_input_fr_simple(label, key, default=0.0, min_value=0.0):
    current = float(st.session_state.get(key, default) or 0.0)
    raw_default = st.session_state.get(f"{key}_raw", f"{current:.2f}".replace(".", ","))
    raw = st.text_input(label, value=raw_default, key=f"{key}_raw")
    try:
        val = float(str(raw).strip().replace(",", "."))
    except Exception:
        val = current
    val = max(min_value, val)
    st.session_state[key] = float(val)
    return val

# ========= Utilitaires métier =========
def calc_pas_cm(V_kN: float, n_brins: int, phi_mm: int, d_cm: float, fyd: float) -> float:
    """
    s_th [cm] = (A_sv * fyd * d_mm) / (V_kN * 10^4)
    avec A_sv = n_brins * pi * (phi/2)^2  [mm²]
    d_mm = d_cm * 10
    """
    if V_kN <= 0 or n_brins <= 0 or phi_mm <= 0 or d_cm <= 0 or fyd <= 0:
        return 0.0
    A_sv = n_brins * math.pi * (phi_mm/2.0)**2   # mm²
    d_mm = d_cm * 10.0
    return (A_sv * fyd * d_mm) / (V_kN * 1e4)    # cm

# ========= Wrapper d’import sécurisé (affiche la vraie ligne fautive) =========
def _import_generateur_pdf():
    try:
        importlib.invalidate_caches()
        from modules.export_pdf import generer_rapport_pdf
        return generer_rapport_pdf
    except SyntaxError as e:
        st.error(f"SyntaxError dans modules/export_pdf.py (ligne {getattr(e,'lineno','?')}, colonne {getattr(e,'offset','?')})")
        bad_line = getattr(e, 'text', '')
        if bad_line:
            st.code(bad_line)
        return None
    except Exception as e:
        st.error("Erreur à l'import de modules/export_pdf.py")
        st.exception(e)
        return None

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
        payload = {k: st.session_state[k] for k in SAVE_KEYS if k in st.session_state}
        st.download_button(
            label="💾 Enregistrer",
            data=json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8"),
            file_name="poutre_ba.json",
            mime="application/json",
            use_container_width=True,
            key="btn_save_dl"
        )

    with btn4:
        if st.button("📂 Ouvrir", use_container_width=True, key="btn_open_toggle"):
            st.session_state["show_open_uploader"] = not st.session_state.get("show_open_uploader", False)

        if st.session_state.get("show_open_uploader", False):
            uploaded = st.file_uploader("Choisir un fichier JSON", type=["json"],
                                        label_visibility="collapsed", key="open_uploader")
            if uploaded is not None:
                data = json.load(uploaded)
                for k, v in data.items():
                    if k in SAVE_KEYS:
                        st.session_state[k] = v
                st.session_state["show_open_uploader"] = False
                st.success("Fichier chargé.")
                st.rerun()

    with btn5:
        if st.button("📄 Générer PDF", use_container_width=True, key="btn_pdf"):
            # from modules.export_pdf import generer_rapport_pdf  # <— remplacé
            gen_pdf = _import_generateur_pdf()
            if gen_pdf is None:
                st.stop()

            # flags explicites pour l’export (pour cacher la partie droite)
            has_sup  = bool(st.session_state.get("ajouter_moment_sup", False) and st.session_state.get("M_sup", 0.0) > 0)
            has_vlim = bool(st.session_state.get("ajouter_effort_reduit", False) and st.session_state.get("V_lim", 0.0) > 0)

            # libellé acier type B500 / B400
            acier_label = f"B{st.session_state.get('fyk','500')}"

            fichier_pdf = gen_pdf(
                # --- en-tête / géométrie / sollicitations
                nom_projet=st.session_state.get("nom_projet", ""),
                partie=st.session_state.get("partie", ""),
                date=st.session_state.get("date", ""),
                indice=st.session_state.get("indice", ""),
                beton=st.session_state.get("beton", ""),
                fyk=st.session_state.get("fyk", ""),
                acier_label=acier_label,          # <— pour afficher B500/B400 dans le tableau
                b=st.session_state.get("b", 0),
                h=st.session_state.get("h", 0),
                enrobage=st.session_state.get("enrobage", 0),

                M_inf=st.session_state.get("M_inf", 0.0),
                M_sup=st.session_state.get("M_sup", 0.0),
                V=st.session_state.get("V", 0.0),
                V_lim=st.session_state.get("V_lim", 0.0),

                # --- CHOIX (→ affichés dans le PDF)
                n_as_inf=st.session_state.get("n_as_inf"),
                o_as_inf=st.session_state.get("ø_as_inf"),
                n_as_sup=st.session_state.get("n_as_sup"),
                o_as_sup=st.session_state.get("ø_as_sup"),

                n_etriers=st.session_state.get("n_etriers"),
                o_etrier=st.session_state.get("ø_etrier"),
                pas_etrier=st.session_state.get("pas_etrier"),

                n_etriers_r=st.session_state.get("n_etriers_r"),
                o_etrier_r=st.session_state.get("ø_etrier_r"),
                pas_etrier_r=st.session_state.get("pas_etrier_r"),

                # flags d’affichage pour masquer complètement la colonne droite
                has_sup=has_sup,
                has_vlim=has_vlim,
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
                              value=st.session_state.get("date", datetime.today().strftime("%d/%m/%Y")), key="date")
            with c2:
                st.text_input("", placeholder="Indice", value=st.session_state.get("indice", "0"), key="indice")
        else:
            st.session_state.setdefault("date", datetime.today().strftime("%d/%m/%Y"))

        st.markdown("### Caractéristiques de la poutre")
        cbet, cacier = st.columns(2)
        with cbet:
            options = list(beton_data.keys())
            default_beton = options[min(2, len(options)-1)]
            current_beton = st.session_state.get("beton", default_beton)
            st.selectbox("Classe de béton", options, index=options.index(current_beton), key="beton")
        with cacier:
            acier_opts = ["400", "500"]
            cur_fyk = st.session_state.get("fyk", "500")
            st.selectbox("Qualité d'acier [N/mm²]", acier_opts, index=acier_opts.index(cur_fyk), key="fyk")

        csec1, csec2, csec3 = st.columns(3)
        with csec1:
            st.number_input("Larg. [cm]", min_value=5, max_value=1000,
                            value=st.session_state.get("b", 20), step=5, key="b")
        with csec2:
            st.number_input("Haut. [cm]", min_value=5, max_value=1000,
                            value=st.session_state.get("h", 40), step=5, key="h")
        with csec3:
            st.number_input("Enrob. (cm)", min_value=0.0, max_value=100.0,
                            value=st.session_state.get("enrobage", 5.0), step=0.5, key="enrobage")

        # Matériaux
        beton = st.session_state["beton"]
        fck       = beton_data[beton]["fck"]
        fck_cube  = beton_data[beton]["fck_cube"]
        alpha_b   = beton_data[beton]["alpha_b"]
        mu_val    = beton_data[beton][f"mu_a{st.session_state['fyk']}"]
        fyd       = int(st.session_state["fyk"]) / 1.5

        st.markdown("### Sollicitations")
        cmom, cev  = st.columns(2)
        with cmom:
            M_inf = float_input_fr_simple("Moment inférieur M (kNm)", key="M_inf", default=0.0, min_value=0.0)
            m_sup = st.checkbox("Ajouter un moment supérieur", key="ajouter_moment_sup",
                                value=st.session_state.get("ajouter_moment_sup", False))
            if m_sup:
                M_sup = float_input_fr_simple("Moment supérieur M_sup (kNm)", key="M_sup", default=0.0, min_value=0.0)
            else:
                M_sup = 0.0
                if "M_sup" in st.session_state:
                    del st.session_state["M_sup"]
        with cev:
            V = float_input_fr_simple("Effort tranchant V (kN)", key="V", default=0.0, min_value=0.0)
            v_sup = st.checkbox("Ajouter un effort tranchant réduit", key="ajouter_effort_reduit",
                                value=st.session_state.get("ajouter_effort_reduit", False))
            if v_sup:
                V_lim = float_input_fr_simple("Effort tranchant réduit V_réduit (kN)", key="V_lim", default=0.0, min_value=0.0)
            else:
                V_lim = 0.0
                if "V_lim" in st.session_state:
                    del st.session_state["V_lim"]

    # ---------- COLONNE DROITE ----------
    with result_col_droite:
        st.markdown("### Dimensionnement")

        # ---- Vérification de la hauteur ----
        M_max      = max(st.session_state.get("M_inf", 0.0), st.session_state.get("M_sup", 0.0))
        b = st.session_state["b"]; h = st.session_state["h"]; enrobage = st.session_state["enrobage"]
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
        M_inf = st.session_state.get("M_inf", 0.0)
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
        n_val = st.session_state.get("n_as_inf", n_inf_cur)
        d_val = st.session_state.get("ø_as_inf", diam_inf_cur)
        As_inf_choisi = n_val * (math.pi * (d_val/2)**2)
        with row1_c3:
            st.markdown(
                f"<div style='margin-top:30px;font-weight:600;white-space:nowrap;'>( {As_inf_choisi:.0f} mm² )</div>",
                unsafe_allow_html=True
        )
        close_bloc()

        # ---- Armatures supérieures (si M_sup) ----
        if st.session_state.get("ajouter_moment_sup", False):
            M_sup = st.session_state.get("M_sup", 0.0)
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
        V = st.session_state.get("V", 0.0)
        tau_1 = 0.016 * fck_cube / 1.05
        tau_2 = 0.032 * fck_cube / 1.05
        tau_4 = 0.064 * fck_cube / 1.05

        if V > 0:
            tau = V * 1e3 / (0.75 * b * h * 100)
            if   tau <= tau_1: besoin, etat_tau, nom_lim, tau_lim = "Pas besoin d’étriers", "ok",  "τ_adm_I",  tau_1
            elif tau <= tau_2: besoin, etat_tau, nom_lim, tau_lim = "Besoin d’étriers",      "ok",  "τ_adm_II", tau_2
            elif tau <= tau_4: besoin, etat_tau, nom_lim, tau_lim = "Besoin de barres inclinées et d’étriers", "warn", "τ_adm_IV", tau_4
            else:              besoin, etat_tau, nom_lim, tau_lim = "Pas acceptable",        "nok", "τ_adm_IV", tau_4

            open_bloc("Vérification de l'effort tranchant", etat_tau)
            st.markdown(f"τ = {tau:.2f} N/mm² ≤ {nom_lim} = {tau_lim:.2f} N/mm² → {besoin}")
            close_bloc()

            # ---- Détermination des étriers
            n_etriers_cur = int(st.session_state.get("n_etriers", 1))   # = nombre d'étriers → 2 brins verticaux
            d_etrier_cur  = int(st.session_state.get("ø_etrier", 8))
            pas_cur       = float(st.session_state.get("pas_etrier", 30.0))

            # calcul propre (unité cm) – on prend 2 brins par étrier
            s_th = calc_pas_cm(V_kN=V, n_brins=2*n_etriers_cur, phi_mm=d_etrier_cur, d_cm=d_utile, fyd=fyd)

            # signe de comparaison théorique vs choisi (s doit être ≤ s_th)
            signe = "≥" if s_th >= pas_cur else "<"
            etat_pas = "ok" if pas_cur <= s_th else ("warn" if pas_cur <= 30 else "nok")

            open_bloc("Détermination des étriers", etat_pas)
            r_val = d_etrier_cur/2.0
            st.markdown(
                f"- Rayon utilisé **r = {r_val:.1f} mm**  \n"
                f"- **s_th = {s_th:.1f} cm**  {signe}  **Pas choisi = {pas_cur:.1f} cm**"
            )
            close_bloc()

        # ---- Vérification effort tranchant réduit ----
        if st.session_state.get("ajouter_effort_reduit", False) and st.session_state.get("V_lim", 0.0) > 0:
            V_lim = st.session_state["V_lim"]
            tau_r = V_lim * 1e3 / (0.75 * b * h * 100)
            if   tau_r <= tau_1: besoin_r, etat_r, nom_lim_r, tau_lim_r = "Pas besoin d’étriers", "ok",  "τ_adm_I",  tau_1
            elif tau_r <= tau_2: besoin_r, etat_r, nom_lim_r, tau_lim_r = "Besoin d’étriers",     "ok",  "τ_adm_II", tau_2
            elif tau_r <= tau_4: besoin_r, etat_r, nom_lim_r, tau_lim_r = "Besoin de barres inclinées et d’étriers", "warn", "τ_adm_IV", tau_4
            else:                 besoin_r, etat_r, nom_lim_r, tau_lim_r = "Pas acceptable",       "nok", "τ_adm_IV", tau_4

            open_bloc("Vérification de l'effort tranchant réduit", etat_r)
            st.markdown(f"τ = {tau_r:.2f} N/mm² ≤ {nom_lim_r} = {tau_lim_r:.2f} N/mm² → {besoin_r}")
            close_bloc()

            # Étriers réduits (même logique)
            n_et_r_cur = int(st.session_state.get("n_etriers_r", 1))
            d_et_r_cur = int(st.session_state.get("ø_etrier_r", 8))
            pas_r_cur  = float(st.session_state.get("pas_etrier_r", 30.0))

            s_thr = calc_pas_cm(V_kN=V_lim, n_brins=2*n_et_r_cur, phi_mm=d_et_r_cur, d_cm=d_utile, fyd=fyd)
            signe_r = "≥" if s_thr >= pas_r_cur else "<"
            etat_pas_r = "ok" if pas_r_cur <= s_thr else ("warn" if pas_r_cur <= 30 else "nok")

            open_bloc("Détermination des étriers réduits", etat_pas_r)
            r_val_r = d_et_r_cur/2.0
            st.markdown(
                f"- Rayon utilisé **r = {r_val_r:.1f} mm**  \n"
                f"- **s_th = {s_thr:.1f} cm**  {signe_r}  **Pas choisi = {pas_r_cur:.1f} cm**"
            )
            close_bloc()

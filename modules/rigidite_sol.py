# modules/rigidite_sol.py
# -------------------------------------------------------------
# Raideur de sol & appuis (SCIA – k en MN/m³)
# - Colonne GAUCHE : entrées + menu des cas + configuration avancée
# - Colonne DROITE : résultats + (option) détail des calculs
# - Méthodes propres : SLS (q,w) / q ad – s adm / E–B–ν
# - Base de connaissances multi-sélection avec surlignage
# -------------------------------------------------------------

import math
import pandas as pd
import streamlit as st

# =============================================================
# ===============  FONCTION D’ENTRÉE DE PAGE  =================
# =============================================================
def show():

    # -----------------------------
    # ⚙️ Page config
    # -----------------------------
    st.set_page_config(page_title="Raideur de sol & appuis", page_icon="🧱", layout="wide")

    # -----------------------------
    # 🎨 Style (proche de ta maquette) + LaTeX à GAUCHE
    # -----------------------------
    STYLES = """
    <style>
    /* Titres & cartes */
    h1, h2, h3 { margin: 0 0 .5rem 0; }
    .section-title { font-size: 1.25rem; font-weight: 700; margin: .25rem 0 .5rem 0; }
    .card { background: white; border-radius: 16px; padding: 1rem 1.25rem; box-shadow: 0 2px 10px rgba(15,23,42,.05); border: 1px solid #EEF2F7; }
    .badge { display:inline-block; padding:.25rem .6rem; border-radius:999px; background:#F5F7FB; color:#334155; font-size:.85rem; }
    .metric-box { background:#F5F7FB; border-radius:12px; padding:.75rem 1rem; border:1px solid #E2E8F0; }
    .small { color:#64748B; font-size:.9rem; }

    /* Boutons topbar */
    .topbar button { border-radius: 12px !important; height: 48px; font-weight: 600; }

    /* LaTeX aligné à gauche (global) */
    .katex-display { text-align:left !important; margin: .25rem 0 .5rem 0 !important; }
    .katex-display > .katex { text-align:left !important; }

    /* Tableau base de connaissances : ligne surlignée */
    .emph { background: #E6F4EA !important; font-weight: 700 !important; color:#14532D !important; }
    </style>
    """
    st.markdown(STYLES, unsafe_allow_html=True)

    # -----------------------------
    # 🧰 Helpers unités & affichage
    # -----------------------------
    def to_kPa_from(value: float, unit: str) -> float:
        """Convertit une pression vers kPa (≡ kN/m²). unit in {"kPa","MPa","kg/cm²"}"""
        if unit == "kPa": return value
        if unit == "MPa": return value * 1000.0
        if unit == "kg/cm²": return value * 98.0665
        return value

    def from_kPa_to(value_kPa: float, unit: str) -> float:
        if unit == "kPa": return value_kPa
        if unit == "MPa": return value_kPa / 1000.0
        if unit == "kg/cm²": return value_kPa / 98.0665
        return value_kPa

    def E_MPa_to_kPa(E_MPa: float) -> float:
        """MPa → kPa (kN/m²). 1 MPa = 1000 kPa"""
        return E_MPa * 1000.0

    def E_GPa_to_kPa(E_GPa: float) -> float:
        """GPa → kPa. 1 GPa = 1e6 kPa"""
        return E_GPa * 1_000_000.0

    def kNpm3_to_MNpm3(val_kNpm3: float) -> float:
        return val_kNpm3 / 1000.0

    def MNpm3_to_kNpm3(val_MNpm3: float) -> float:
        return val_MNpm3 * 1000.0

    def param_table(rows):
        """rows = [{'sym':'q', 'desc':'Pression de service', 'val':100, 'unit':'kPa'}, ...]"""
        df = pd.DataFrame(rows, columns=["Paramètre", "Description", "Valeur", "Unité"])
        st.table(df)

    # -----------------------------
    # 🧠 State & valeurs par défaut
    # -----------------------------
    if "press_unit" not in st.session_state:  st.session_state.press_unit = "kPa"
    if "module_unit" not in st.session_state: st.session_state.module_unit = "MPa"
    if "detail_calc" not in st.session_state: st.session_state.detail_calc = True
    if "adv_open" not in st.session_state:    st.session_state.adv_open = False

    # -----------------------------
    # 🧭 Barre du haut
    # -----------------------------
    col_top = st.columns([1,1,1,1,1,1])
    with col_top[0]:
        st.button("🏠 Accueil", use_container_width=True, key="home_btn")
    with col_top[1]:
        if st.button("🧹 Réinitialiser", use_container_width=True, key="reset_btn"):
            keep = {"press_unit","module_unit","detail_calc","adv_open"}
            for k in list(st.session_state.keys()):
                if k not in keep: st.session_state.pop(k, None)
            st.experimental_rerun()
    with col_top[2]:
        st.button("💾 Enregistrer", use_container_width=True)
    with col_top[3]:
        st.button("📂 Ouvrir", use_container_width=True)
    with col_top[4]:
        st.button("📝 Générer PDF", use_container_width=True)
    with col_top[5]:
        st.markdown("<span class='badge'>v1.1</span>", unsafe_allow_html=True)

    st.divider()

    # -----------------------------
    # 🧱 En-tête
    # -----------------------------
    st.markdown("# Raideur de sol & appuis (SCIA – k en MN/m³)")
    st.markdown(
        "<div class='small'>Choisissez un cas à gauche, saisissez les données, et lisez les résultats à droite. "
        "Activez « Détail des calculs » pour voir formules et paramètres.</div>",
        unsafe_allow_html=True
    )
    st.markdown("\n")

    # -----------------------------
    # 🧭 Deux colonnes
    # -----------------------------
    col_left, col_right = st.columns([0.50, 0.50])

    # =============================================================
    # ================         COLONNE GAUCHE        ==============
    # =============================================================
    with col_left:
        st.markdown("### Informations et entrées")

        # --- Bloc Configuration avancée ---
        with st.container(border=True):
            st.markdown("**⚙️ Configuration avancée**")
            st.session_state.adv_open = st.checkbox("Afficher la configuration avancée (unités, options)", value=st.session_state.adv_open)
            if st.session_state.adv_open:
                c1, c2 = st.columns(2)
                with c1:
                    st.session_state.press_unit = st.selectbox(
                        "Pressions / contraintes", ["kPa","MPa","kg/cm²"],
                        index=["kPa","MPa","kg/cm²"].index(st.session_state.press_unit)
                    )
                with c2:
                    st.session_state.module_unit = st.selectbox(
                        "Modules E", ["MPa","GPa"],
                        index=0 if st.session_state.module_unit=="MPa" else 1
                    )

        # --- Choix du cas ---
        with st.container(border=True):
            st.markdown("**Choix du cas**")
            cas = st.selectbox(
                "Quel cas souhaitez-vous traiter ?",
                (
                    "1. Sol homogène",
                    "2. Sol multicouche",
                    "3. CPT / empirique",
                    "4. Plat métallique sur béton",
                    "5. Convertisseur & vérification",
                    "6. Base de connaissances (types de sols)",
                ),
                index=0,
            )

        # -------------------------
        # Formulaires selon le cas
        # -------------------------
        if cas.startswith("1"):
            st.markdown("**Sol homogène — méthode**")
            method = st.radio(
                "Sélectionnez la méthode",
                ["SLS direct (q, w)", "Depuis contrainte admissible (q ad, s adm)", "Depuis module E (E, B, ν)"],
                horizontal=True
            )

            if method.startswith("SLS"):
                c1, c2 = st.columns(2)
                with c1:
                    st.session_state.solo_q = st.number_input(
                        f"q (pression de service) [{st.session_state.press_unit}]",
                        min_value=0.0, value=60.0, step=5.0
                    )
                with c2:
                    st.session_state.solo_w = st.number_input(
                        "w (tassement) [mm]",
                        min_value=0.001, value=25.0, step=1.0
                    )

            elif method.startswith("Depuis contrainte"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.session_state.solo_qad = st.number_input(
                        f"q ad [{st.session_state.press_unit}]",
                        min_value=0.0, value=100.0, step=5.0
                    )
                with c2:
                    st.session_state.solo_sadm = st.number_input("s adm [mm]", min_value=0.1, value=25.0, step=1.0)
                with c3:
                    st.session_state.solo_isult = st.toggle("q ad est une contrainte ultime ?", value=False)
                    st.session_state.solo_sf = st.number_input("SF (si ultime)", min_value=1.0, value=3.0, step=0.5)

            else:  # Depuis module E
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.session_state.module_unit == "MPa":
                        st.session_state.solo_E = st.number_input("E du sol [MPa]", min_value=0.0, value=80.0, step=5.0)
                    else:
                        st.session_state.solo_E = st.number_input("E du sol [GPa]", min_value=0.0, value=0.08, step=0.01)
                with c2:
                    st.session_state.solo_B = st.number_input("B (largeur caractéristique) [m]", min_value=0.01, value=2.0, step=0.1)
                with c3:
                    st.session_state.solo_nu = st.number_input("ν (Poisson)", min_value=0.0, max_value=0.49, value=0.30, step=0.01)

        elif cas.startswith("2"):
            st.markdown("**Sol multicouche — données**")
            n = int(st.number_input("Nombre de couches", min_value=1, value=3, step=1))
            if "multi_layers" not in st.session_state or len(st.session_state.multi_layers) != n:
                st.session_state.multi_layers = [{"h": 1.0, "E": 30.0} for _ in range(n)]
            for i in range(n):
                c1, c2 = st.columns(2)
                with c1:
                    st.session_state.multi_layers[i]["h"] = st.number_input(
                        f"h{i+1} (épaisseur) [m]",
                        min_value=0.01, value=float(st.session_state.multi_layers[i]["h"]), step=0.1, key=f"multi_h_{i}"
                    )
                with c2:
                    if st.session_state.module_unit == "MPa":
                        st.session_state.multi_layers[i]["E"] = st.number_input(
                            f"E{i+1} [{st.session_state.module_unit}]",
                            min_value=0.0, value=float(st.session_state.multi_layers[i]["E"]), step=5.0, key=f"multi_E_{i}"
                        )
                    else:
                        Eg = st.number_input(f"E{i+1} [GPa]", min_value=0.0,
                                             value=float(st.session_state.multi_layers[i]["E"]/1000.0),
                                             step=0.1, key=f"multi_Eg_{i}")
                        st.session_state.multi_layers[i]["E"] = Eg * 1000.0
            st.markdown("**Option d'échelle**")
            c1, c2 = st.columns(2)
            with c1:
                st.session_state.multi_scale = st.toggle("Appliquer l'effet de largeur B", value=False)
            with c2:
                st.session_state.multi_B = st.number_input("B (m)", min_value=0.01, value=2.0, step=0.1) if st.session_state.multi_scale else None
            if st.session_state.multi_scale:
                st.session_state.multi_nu = st.number_input("ν moyen", min_value=0.0, max_value=0.49, value=0.30, step=0.01)

        elif cas.startswith("3"):
            st.markdown("**CPT / empirique**")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.session_state.cpt_qt = st.number_input("q_t (MPa)", min_value=0.0, value=10.0, step=0.5)
            with c2:
                st.session_state.cpt_sv0 = st.number_input("σ'v0 (kPa)", min_value=0.0, value=50.0, step=5.0)
            with c3:
                st.session_state.cpt_alphaE = st.number_input("α_E (5–10)", min_value=1.0, value=8.0, step=0.5)
            with c4:
                st.session_state.cpt_B = st.number_input("B (m)", min_value=0.01, value=2.0, step=0.1)
            st.session_state.cpt_nu = st.slider("ν (Poisson)", min_value=0.2, max_value=0.45, value=0.30, step=0.01)

        elif cas.startswith("4"):
            st.markdown("**Plat métallique sur béton**")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.session_state.plate_B = st.number_input("B plat (mm)", min_value=10.0, value=200.0, step=10.0)
            with c2:
                st.session_state.plate_L = st.number_input("L plat (mm)", min_value=10.0, value=200.0, step=10.0)
            with c3:
                st.session_state.plate_alpha = st.slider("α (h_c = α·min(B,L))", min_value=0.3, max_value=0.8, value=0.5, step=0.05)
            c4, c5, c6 = st.columns(3)
            with c4:
                st.session_state.plate_Ec = st.number_input("E béton (GPa)", min_value=1.0, value=30.0, step=1.0)
            with c5:
                st.session_state.plate_use_nu = st.toggle("Inclure (1-ν²)?", value=False)
            with c6:
                st.session_state.plate_nu = st.number_input("ν béton", min_value=0.0, max_value=0.49, value=0.20, step=0.01)
            st.markdown("**Mortier / résine (option)**")
            c7, c8, c9 = st.columns(3)
            with c7:
                st.session_state.plate_has_grout = st.toggle("Avec mortier/résine", value=True)
            with c8:
                st.session_state.plate_Eg = st.number_input("E mortier (GPa)", min_value=0.5, value=12.0, step=0.5) if st.session_state.plate_has_grout else 0.0
            with c9:
                st.session_state.plate_tg = st.number_input("t_g (mm)", min_value=0.1, value=10.0, step=0.5) if st.session_state.plate_has_grout else 0.0

        elif cas.startswith("5"):
            st.markdown("**Convertisseur & vérification**")
            c1, c2, c3 = st.columns(3)
            with c1: p_kg = st.number_input("kg/cm²", min_value=0.0, value=1.0, step=0.1)
            with c2: p_kPa = st.number_input("kPa",     min_value=0.0, value=98.0665, step=1.0)
            with c3: p_MPa = st.number_input("MPa",     min_value=0.0, value=0.0980665, step=0.01)
            col_sync = st.columns(3)
            with col_sync[0]:
                if st.button("← depuis kg/cm²", use_container_width=True):
                    st.session_state.u_kPa = p_kg * 98.0665
                    st.session_state.u_MPa = p_kg * 0.0980665
            with col_sync[1]:
                if st.button("← depuis kPa", use_container_width=True):
                    st.session_state.u_kg = p_kPa / 98.0665
                    st.session_state.u_MPa = p_kPa / 1000.0
            with col_sync[2]:
                if st.button("← depuis MPa", use_container_width=True):
                    st.session_state.u_kPa = p_MPa * 1000.0
                    st.session_state.u_kg = (p_MPa * 1000.0) / 98.0665
            st.markdown("**Contrôle rapide q→w**")
            c1, c2 = st.columns(2)
            with c1: q_ctrl = st.number_input("q (kPa)",  min_value=0.0, value=100.0, step=10.0)
            with c2: k_ctrl = st.number_input("k (MN/m³)", min_value=0.001, value=10.0,  step=1.0)
            w_ctrl_mm = (q_ctrl / MNpm3_to_kNpm3(k_ctrl)) * 1000.0  # mm
            st.info(f"w = q/k = **{w_ctrl_mm:.2f} mm**")

        else:  # 6 — Base de connaissances
            st.markdown("**Base de connaissances – Types de sols (sélection multiple)**")
            SOILS = [
                {"Type":"Argile très molle","Desc":"Très humide, pâteuse, tassements importants.","E(MPa)":8,"k_s(MN/m³)":"1–3","q ad(kg/cm²)":"0.10–0.20","γ(kN/m³)":"16–18"},
                {"Type":"Argile molle","Desc":"Cohésive, plasticité marquée, consolidation différée.","E(MPa)":15,"k_s(MN/m³)":"2–5","q ad(kg/cm²)":"0.20–0.50","γ(kN/m³)":"18–19"},
                {"Type":"Limon meuble","Desc":"Silt/argile/sable, sensible à l'eau.","E(MPa)":25,"k_s(MN/m³)":"3–8","q ad(kg/cm²)":"0.30–0.80","γ(kN/m³)":"17–19"},
                {"Type":"Limon compact","Desc":"Sablo-limoneux compact, portance moyenne.","E(MPa)":40,"k_s(MN/m³)":"8–15","q ad(kg/cm²)":"0.80–1.50","γ(kN/m³)":"18–20"},
                {"Type":"Sable meuble","Desc":"Peu compact, tassements immédiats.","E(MPa)":40,"k_s(MN/m³)":"8–12","q ad(kg/cm²)":"0.50–1.00","γ(kN/m³)":"17–19"},
                {"Type":"Sable dense","Desc":"Grains serrés, bon porteur.","E(MPa)":80,"k_s(MN/m³)":"15–30","q ad(kg/cm²)":"1.00–2.00","γ(kN/m³)":"18–20"},
                {"Type":"Sable graveleux","Desc":"Très drainant, très bon appui.","E(MPa)":120,"k_s(MN/m³)":"30–50","q ad(kg/cm²)":"2.00–3.00","γ(kN/m³)":"19–21"},
                {"Type":"Gravier compact","Desc":"Matériaux grossiers compactés.","E(MPa)":200,"k_s(MN/m³)":"50–80","q ad(kg/cm²)":"3.00–5.00","γ(kN/m³)":"20–22"},
                {"Type":"Marne / Moraine","Desc":"Calcaire/glaciaire cohérent, rigide.","E(MPa)":300,"k_s(MN/m³)":"80–150","q ad(kg/cm²)":"5.00–8.00","γ(kN/m³)":"21–23"},
                {"Type":"Roche tendre","Desc":"Matériau fissuré mais porteur.","E(MPa)":500,"k_s(MN/m³)":"150–300","q ad(kg/cm²)":"8.00–15.00","γ(kN/m³)":"22–24"},
                {"Type":"Roche dure / Béton","Desc":"Quasi indéformable.","E(MPa)":1000,"k_s(MN/m³)":"300–800","q ad(kg/cm²)":"15.00–30.00","γ(kN/m³)":"24–27"},
            ]
            df_soils = pd.DataFrame(SOILS)
            choices = st.multiselect(
                "Sélectionnez un ou plusieurs types de sols à mettre en évidence",
                options=list(df_soils["Type"]), default=[]
            )
            # Ajout colonne ✓ sélectionné
            df_view = df_soils.copy()
            df_view["✓ sélectionné"] = df_view["Type"].apply(lambda x: "✓" if x in choices else "")
            # Styler avec mise en évidence des lignes choisies
            def highlight_rows(row):
                return ['emph' if row["Type"] in choices else '' for _ in row]
            st.table(df_view.style.apply(highlight_rows, axis=1))

    # =============================================================
    # ================        COLONNE DROITE         ==============
    # =============================================================
    with col_right:
        st.markdown("### Dimensionnement / Résultats")

        # Interrupteur détail des calculs
        top_cols = st.columns([0.5, 0.5])
        with top_cols[0]:
            st.session_state.detail_calc = st.checkbox("📘 Détail des calculs (formules + paramètres)", value=st.session_state.detail_calc)

        with st.container(border=True):

            # ---------- CAS 1 : Sol homogène ----------
            if cas.startswith("1"):
                # SLS direct
                if "solo_q" in st.session_state and "solo_w" in st.session_state and st.session_state.solo_w:
                    q_kPa = to_kPa_from(st.session_state.solo_q, st.session_state.press_unit)
                    w_m  = st.session_state.solo_w / 1000.0
                    ksA  = kNpm3_to_MNpm3(q_kPa / w_m)
                    st.metric("k (MN/m³)", f"{ksA:,.2f}")
                    if st.session_state.detail_calc:
                        st.latex(r"k = \dfrac{q}{w}")
                        param_table([
                            {"Paramètre":"q","Description":"Pression de service","Valeur":f"{st.session_state.solo_q:,.3f}","Unité":st.session_state.press_unit},
                            {"Paramètre":"w","Description":"Tassement","Valeur":f"{st.session_state.solo_w:,.3f}","Unité":"mm"},
                            {"Paramètre":"k","Description":"Raideur de sol","Valeur":f"{ksA:,.3f}","Unité":"MN/m³"},
                        ])

                # Depuis contrainte admissible
                if "solo_qad" in st.session_state and "solo_sadm" in st.session_state:
                    sadm_m = st.session_state.solo_sadm / 1000.0
                    qad_kPa = to_kPa_from(st.session_state.solo_qad, st.session_state.press_unit)
                    qad_used = qad_kPa * (st.session_state.solo_sf if st.session_state.solo_isult else 1.0)
                    if sadm_m > 0:
                        ksB = kNpm3_to_MNpm3(qad_used / sadm_m)
                        st.metric("k (MN/m³)", f"{ksB:,.2f}")
                        if st.session_state.detail_calc:
                            st.latex(r"k = \dfrac{q^{ad}}{s^{adm}} \quad \text{(ou } k = \dfrac{SF \cdot q^{ad}}{s^{adm}}\text{ si ultime)}")
                            param_table([
                                {"Paramètre":"q ad","Description":"Contrainte admissible (ou ultime × SF)","Valeur":f"{from_kPa_to(qad_used, st.session_state.press_unit):,.3f}","Unité":st.session_state.press_unit},
                                {"Paramètre":"s adm","Description":"Tassement admissible","Valeur":f"{st.session_state.solo_sadm:,.3f}","Unité":"mm"},
                                {"Paramètre":"SF","Description":"Facteur de sécurité (si q ad ultime)","Valeur":f"{st.session_state.solo_sf:,.2f}" if st.session_state.solo_isult else "—","Unité":"—"},
                                {"Paramètre":"k","Description":"Raideur de sol","Valeur":f"{ksB:,.3f}","Unité":"MN/m³"},
                            ])

                # Depuis E
                if "solo_E" in st.session_state and "solo_B" in st.session_state:
                    E_input = st.session_state.solo_E
                    E_MPa = E_input if st.session_state.module_unit=="MPa" else (E_input*1000.0)
                    E_kPa = E_MPa_to_kPa(E_MPa)
                    B     = max(st.session_state.solo_B, 1e-6)
                    nu    = st.session_state.solo_nu
                    ksC   = kNpm3_to_MNpm3(E_kPa / (B * (1 - nu**2)))
                    st.metric("k (MN/m³)", f"{ksC:,.2f}")
                    if st.session_state.detail_calc:
                        st.latex(r"k = \dfrac{E}{B\,(1-\nu^2)}")
                        param_table([
                            {"Paramètre":"E","Description":"Module de Young du sol","Valeur":f"{E_MPa:,.3f}","Unité":"MPa"},
                            {"Paramètre":"B","Description":"Largeur caractéristique de la dalle/semelle","Valeur":f"{B:,.3f}","Unité":"m"},
                            {"Paramètre":"ν","Description":"Coefficient de Poisson","Valeur":f"{nu:,.3f}","Unité":"—"},
                            {"Paramètre":"k","Description":"Raideur de sol","Valeur":f"{ksC:,.3f}","Unité":"MN/m³"},
                        ])

            # ---------- CAS 2 : Sol multicouche ----------
            elif cas.startswith("2"):
                layers = st.session_state.multi_layers
                denom = 0.0
                H = 0.0
                for lay in layers:
                    h = float(lay['h'])
                    H += h
                    E_MPa = float(lay['E'])
                    E_kPa = E_MPa_to_kPa(E_MPa)
                    if E_kPa > 0: denom += h / E_kPa
                ks_eq = kNpm3_to_MNpm3((1.0/denom) if denom>0 else 0.0)
                st.metric("k_eq (MN/m³)", f"{ks_eq:,.2f}")
                if st.session_state.detail_calc:
                    st.latex(r"k_{eq} = \left( \sum_i \dfrac{h_i}{E_i} \right)^{-1}")
                    param_table([
                        {"Paramètre":"H","Description":"Somme des épaisseurs","Valeur":f"{H:,.3f}","Unité":"m"},
                        {"Paramètre":"k_eq","Description":"Raideur équivalente (par unité de surface)","Valeur":f"{ks_eq:,.3f}","Unité":"MN/m³"},
                    ])
                if st.session_state.get("multi_scale"):
                    Eeq_kPa = (ks_eq*1000.0) * H  # k_eq (MN/m³)->kN/m³ * H = kPa
                    Bm  = st.session_state.multi_B
                    nu  = st.session_state.multi_nu
                    ksB = kNpm3_to_MNpm3(Eeq_kPa / (Bm * (1 - nu**2)))
                    st.metric("k (avec échelle B) (MN/m³)", f"{ksB:,.2f}")
                    if st.session_state.detail_calc:
                        st.latex(r"E_{eq} = k_{eq}\,H \quad;\quad k \approx \dfrac{E_{eq}}{B\,(1-\nu^2)}")
                        param_table([
                            {"Paramètre":"E_eq","Description":"Module équivalent","Valeur":f"{Eeq_kPa/1000.0:,.3f}","Unité":"MPa"},
                            {"Paramètre":"B","Description":"Largeur caractéristique","Valeur":f"{Bm:,.3f}","Unité":"m"},
                            {"Paramètre":"ν","Description":"Coefficient de Poisson (moyen)","Valeur":f"{nu:,.3f}","Unité":"—"},
                            {"Paramètre":"k","Description":"Raideur avec échelle B","Valeur":f"{ksB:,.3f}","Unité":"MN/m³"},
                        ])

            # ---------- CAS 3 : CPT / empirique ----------
            elif cas.startswith("3"):
                qt_kPa = st.session_state.cpt_qt * 1000.0
                E_kPa  = st.session_state.cpt_alphaE * max(qt_kPa - st.session_state.cpt_sv0, 0.0)
                E_MPa  = E_kPa / 1000.0
                ks     = kNpm3_to_MNpm3(E_kPa / (st.session_state.cpt_B * (1 - st.session_state.cpt_nu**2)))
                c1, c2 = st.columns(2)
                c1.metric("E estimé (MPa)", f"{E_MPa:,.1f}")
                c2.metric("k (MN/m³)", f"{ks:,.2f}")
                if st.session_state.detail_calc:
                    st.latex(r"E = \alpha_E\,(q_t-\sigma'_{v0}) \quad;\quad k = \dfrac{E}{B\,(1-\nu^2)}")
                    param_table([
                        {"Paramètre":"q_t","Description":"Résistance de pointe (CPT)","Valeur":f"{st.session_state.cpt_qt:,.3f}","Unité":"MPa"},
                        {"Paramètre":"σ'v0","Description":"Contrainte verticale effective","Valeur":f"{st.session_state.cpt_sv0:,.3f}","Unité":"kPa"},
                        {"Paramètre":"α_E","Description":"Coefficient empirique (5–10)","Valeur":f"{st.session_state.cpt_alphaE:,.2f}","Unité":"—"},
                        {"Paramètre":"B","Description":"Largeur caractéristique","Valeur":f"{st.session_state.cpt_B:,.3f}","Unité":"m"},
                        {"Paramètre":"ν","Description":"Coefficient de Poisson","Valeur":f"{st.session_state.cpt_nu:,.3f}","Unité":"—"},
                        {"Paramètre":"k","Description":"Raideur du sol","Valeur":f"{ks:,.3f}","Unité":"MN/m³"},
                    ])

            # ---------- CAS 4 : Plat métallique sur béton ----------
            elif cas.startswith("4"):
                Bp = st.session_state.plate_B / 1000.0
                Lp = st.session_state.plate_L / 1000.0
                hc = st.session_state.plate_alpha * min(Bp, Lp)
                Ec_kPa = E_GPa_to_kPa(st.session_state.plate_Ec)
                kc_kNpm3 = Ec_kPa / (hc * (1 - st.session_state.plate_nu**2)) if st.session_state.plate_use_nu else Ec_kPa / hc
                if st.session_state.plate_has_grout and st.session_state.plate_tg > 0:
                    Eg_kPa = E_GPa_to_kPa(st.session_state.plate_Eg)
                    tg_m   = st.session_state.plate_tg / 1000.0
                    kg_kNpm3 = Eg_kPa / tg_m
                    keq_kNpm3 = 1.0 / (1.0/kc_kNpm3 + 1.0/kg_kNpm3)
                else:
                    keq_kNpm3 = kc_kNpm3
                keq = kNpm3_to_MNpm3(keq_kNpm3)
                c1, c2, c3 = st.columns(3)
                c1.metric("h_c (m)", f"{hc:,.3f}")
                c2.metric("k_c (MN/m³)", f"{kNpm3_to_MNpm3(kc_kNpm3):,.1f}")
                c3.metric("k_eq (MN/m³)", f"{keq:,.1f}")
                if st.session_state.detail_calc:
                    st.latex(r"k_c = \dfrac{E_c}{h_c} \quad;\quad k_g = \dfrac{E_g}{t_g} \quad;\quad \dfrac{1}{k_{eq}} = \dfrac{1}{k_c} + \dfrac{1}{k_g}")
                    param_table([
                        {"Paramètre":"B, L","Description":"Dimensions du plat","Valeur":f"{Bp*1000:.0f}×{Lp*1000:.0f}","Unité":"mm"},
                        {"Paramètre":"h_c","Description":"Profondeur efficace α·min(B,L)","Valeur":f"{hc:,.3f}","Unité":"m"},
                        {"Paramètre":"E_c","Description":"Module du béton","Valeur":f"{st.session_state.plate_Ec:,.1f}","Unité":"GPa"},
                        {"Paramètre":"E_g","Description":"Module du mortier/résine","Valeur":f"{st.session_state.plate_Eg if st.session_state.plate_has_grout else 0:,.1f}","Unité":"GPa"},
                        {"Paramètre":"t_g","Description":"Épaisseur mortier","Valeur":f"{st.session_state.plate_tg if st.session_state.plate_has_grout else 0:,.2f}","Unité":"mm"},
                        {"Paramètre":"ν","Description":"Poisson du béton (si utilisé)","Valeur":f"{st.session_state.plate_nu if st.session_state.plate_use_nu else 0:,.2f}","Unité":"—"},
                        {"Paramètre":"k_eq","Description":"Raideur équivalente de contact","Valeur":f"{keq:,.3f}","Unité":"MN/m³"},
                    ])

            # ---------- CAS 5 : Convertisseur ----------
            elif cas.startswith("5"):
                st.info("Utilisez le bloc de gauche pour convertir les unités et le contrôle q→w.")

            # ---------- CAS 6 : Guide ----------
            else:
                st.warning("Choisissez/filtrez les sols à gauche. Les lignes sélectionnées sont surlignées en vert dans le tableau.")
        
        # ---- Notes & rappels (dynamiques) ----
        with st.expander("Notes & rappels"):
            if cas.startswith("1"):
                st.markdown(
                    "- **SLS direct** : on utilise un couple (q, w) issu d’un tableau de tassements ou de mesures ; "
                    "c’est la méthode la plus représentative pour un modèle Winkler linéaire (k = q / w)."
                    "\n- **Contrainte admissible** : si l’étude fournit une contrainte admissible **q ad** associée à un "
                    "tassement admissible **s adm**, on prend **k = q ad / s adm** (si **q ad** est ultime, on applique **SF**)."
                    "\n- **Module E** : approche théorique sur demi-espace élastique : **k = E / (B·(1−ν²))** ; "
                    "penser à l’effet d’échelle avec **B**."
                )
            elif cas.startswith("2"):
                st.markdown(
                    "- **Multicouche** : sommation série **(1/k_eq) = Σ(h_i/E_i)** ; "
                    "optionnellement, convertir en **k** pour une largeur **B** via **E_eq = k_eq·H**, puis **k ≈ E_eq/[B·(1−ν²)]**."
                )
            elif cas.startswith("3"):
                st.markdown(
                    "- **CPT** : corrélation **E = α_E·(q_t − σ'v0)** ; "
                    "on en déduit **k = E / (B·(1−ν²))**. Ajuster **α_E** selon le type de sol."
                )
            elif cas.startswith("4"):
                st.markdown(
                    "- **Contact plat–béton** : ressorts en série (béton + mortier). **k_c = E_c/h_c**, **k_g = E_g/t_g**, "
                    "puis **1/k_eq = 1/k_c + 1/k_g**."
                )
            else:
                st.markdown(
                    "- Les valeurs guides proviennent de références reconnues (Bowles, NAVFAC, etc.). "
                    "Toujours caler sur l’étude géotechnique locale quand elle existe."
                )

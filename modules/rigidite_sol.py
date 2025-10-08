# app_ks.py
# -------------------------------------------------------------
# Application Streamlit pour calculer la raideur de fondation k_s
# (MN/m³) et la raideur d'appui local (plat métallique sur béton),
# en reprenant la logique et le style de l'écran "Poutre en béton armé" :
# - Colonne GAUCHE : données + options
# - Colonne DROITE : résultats + (option) formules LaTeX alignées à gauche
# - Menu déroulant pour choisir l'un des 6 cas
# - Gestion d'unités : kPa / kg/cm² (pressions), MPa / GPa (modules)
# - Page "Base de connaissances" (sols) avec descriptions simples
# -------------------------------------------------------------

import math
import streamlit as st

st.set_page_config(page_title="Raideur de sol & appuis", page_icon="🧱", layout="wide")

# -----------------------------
# 🎨 Style (proche de ta maquette)
# -----------------------------
STYLES = """
<style>
/***** titres *****/
h1, h2, h3 { margin: 0 0 .5rem 0; }
.section-title { font-size: 1.25rem; font-weight: 700; margin: .25rem 0 .5rem 0; }
.card { background: white; border-radius: 16px; padding: 1rem 1.25rem; box-shadow: 0 2px 10px rgba(15,23,42,.05); border: 1px solid #EEF2F7; }
.badge { display:inline-block; padding:.25rem .6rem; border-radius:999px; background:#F5F7FB; color:#334155; font-size:.85rem; }
.metric-box { background:#F5F7FB; border-radius:12px; padding: .75rem 1rem; border:1px solid #E2E8F0; }

/***** boutons d'en-tête *****/
.topbar button { border-radius: 12px !important; height: 48px; font-weight: 600; }

/***** LaTeX aligné à gauche *****/
/* Streamlit centre KaTeX par défaut via .katex-display { text-align: center }  */
/* On force l'alignement gauche et on annule la marge à gauche */
.block-left .katex-display { text-align:left !important; margin: .25rem 0 .5rem 0 !important; }

/***** petits ajustements *****/
.small { color:#64748B; font-size:.9rem; }
</style>
"""

st.markdown(STYLES, unsafe_allow_html=True)

# -----------------------------
# 🧰 Helpers unités & affichage
# -----------------------------

def to_kPa_from(value: float, unit: str) -> float:
    """Convertit une pression vers kPa (≡ kN/m²). unit in {"kPa","MPa","kg/cm²"}"""
    if unit == "kPa":
        return value
    if unit == "MPa":
        return value * 1000.0
    if unit == "kg/cm²":
        return value * 98.0665
    return value


def from_kPa_to(value_kPa: float, unit: str) -> float:
    if unit == "kPa":
        return value_kPa
    if unit == "MPa":
        return value_kPa / 1000.0
    if unit == "kg/cm²":
        return value_kPa / 98.0665
    return value_kPa


def E_MPa_to_kNpm2(E_MPa: float) -> float:
    """MPa → kN/m² (kPa). 1 MPa = 1000 kPa"""
    return E_MPa * 1000.0


def E_GPa_to_kNpm2(E_GPa: float) -> float:
    """GPa → kN/m². 1 GPa = 1e6 kN/m²"""
    return E_GPa * 1_000_000.0


def kNpm3_to_MNpm3(val_kNpm3: float) -> float:
    return val_kNpm3 / 1000.0


def MNpm3_to_kNpm3(val_MNpm3: float) -> float:
    return val_MNpm3 * 1000.0


def latex_left(expr: str):
    """Affiche une formule LaTeX alignée à gauche."""
    st.markdown(f"<div class='block-left'>$$\displaystyle {expr} $$</div>", unsafe_allow_html=True)

# -----------------------------
# 🧠 State & préférences
# -----------------------------
if "show_formulas" not in st.session_state:
    st.session_state.show_formulas = True
if "press_unit" not in st.session_state:
    st.session_state.press_unit = "kPa"  # kPa par défaut pour q, q_ad
if "module_unit" not in st.session_state:
    st.session_state.module_unit = "MPa"  # MPa pour E

# -----------------------------
# 🧭 Barre du haut (style buttons)
# -----------------------------
col_top = st.columns([1,1,1,1,1,1])
with col_top[0]:
    st.button("🏠 Accueil", use_container_width=True, key="home_btn")
with col_top[1]:
    if st.button("🧹 Réinitialiser", use_container_width=True, key="reset_btn"):
        for k in list(st.session_state.keys()):
            if k not in ("press_unit","module_unit","show_formulas"):
                st.session_state.pop(k, None)
with col_top[2]:
    st.button("💾 Enregistrer", use_container_width=True)
with col_top[3]:
    st.button("📂 Ouvrir", use_container_width=True)
with col_top[4]:
    st.button("📝 Générer PDF", use_container_width=True)
with col_top[5]:
    st.markdown("<span class='badge'>v1.0</span>", unsafe_allow_html=True)

st.divider()

# -----------------------------
# 🧱 En-tête
# -----------------------------
st.markdown("# Raideur de sol & appuis (SCIA – k en MN/m³)")
st.markdown("<div class='small'>Choisissez un cas à gauche, saisissez les données, et lisez les résultats à droite. Les formules peuvent être affichées/masquées.</div>", unsafe_allow_html=True)

st.markdown("\n")

# -----------------------------
# 🧭 Sélection du cas (1→6)
# -----------------------------
col_left, col_right = st.columns([0.48, 0.52])

with col_left:
    st.markdown("### Informations et entrées")

    with st.container(border=True):
        # Bloc unités & options
        st.markdown("**Unités & options**")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.session_state.press_unit = st.selectbox("Pressions / contraintes", ["kPa","MPa","kg/cm²"], index=["kPa","MPa","kg/cm²"].index(st.session_state.press_unit))
        with c2:
            st.session_state.module_unit = st.selectbox("Modules E", ["MPa","GPa"], index=0 if st.session_state.module_unit=="MPa" else 1)
        with c3:
            st.session_state.show_formulas = st.toggle("Afficher les formules", value=st.session_state.show_formulas)

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
        st.markdown("**Sol homogène — Méthode**")
        method = st.radio("Choisir la méthode", ["A. SLS direct (q & w)", "B. Depuis q_ad", "C. Depuis E"], horizontal=True)

        if method.startswith("A"):
            c1, c2 = st.columns(2)
            with c1:
                q_val = st.number_input(f"q (pression de service) [{st.session_state.press_unit}]", min_value=0.0, value=60.0, step=5.0, key="solo_q")
            with c2:
                w_mm = st.number_input("w (tassement) [mm]", min_value=0.001, value=25.0, step=1.0, key="solo_w")

        elif method.startswith("B"):
            c1, c2, c3 = st.columns(3)
            with c1:
                qa = st.number_input(f"q_ad [{st.session_state.press_unit}]", min_value=0.0, value=100.0, step=5.0, key="solo_qa")
            with c2:
                s_adm_mm = st.number_input("s_adm [mm]", min_value=0.1, value=25.0, step=1.0, key="solo_sadm")
            with c3:
                is_ult = st.toggle("q_ad est ultime ?", value=False, key="solo_isult")
                SF = st.number_input("SF (si ultime)", min_value=1.0, value=3.0, step=0.5, key="solo_sf")

        else:  # C depuis E
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.session_state.module_unit == "MPa":
                    E_val = st.number_input("E du sol [MPa]", min_value=0.0, value=80.0, step=5.0, key="solo_E")
                else:
                    E_val = st.number_input("E du sol [GPa]", min_value=0.0, value=0.08, step=0.01, key="solo_E")
            with c2:
                B = st.number_input("B (largeur caractéristique) [m]", min_value=0.01, value=2.0, step=0.1, key="solo_B")
            with c3:
                nu = st.number_input("ν (Poisson)", min_value=0.0, max_value=0.49, value=0.30, step=0.01, key="solo_nu")

    elif cas.startswith("2"):
        st.markdown("**Sol multicouche — données**")
        n = int(st.number_input("Nombre de couches", min_value=1, value=3, step=1, key="multi_n"))
        if "multi_layers" not in st.session_state or len(st.session_state.multi_layers) != n:
            st.session_state.multi_layers = [{"h": 1.0, "E": 30.0} for _ in range(n)]
        for i in range(n):
            c1, c2 = st.columns(2)
            with c1:
                st.session_state.multi_layers[i]["h"] = st.number_input(f"h{i+1} (épaisseur) [m]", min_value=0.01, value=float(st.session_state.multi_layers[i]["h"]), step=0.1, key=f"multi_h_{i}")
            with c2:
                if st.session_state.module_unit == "MPa":
                    st.session_state.multi_layers[i]["E"] = st.number_input(f"E{i+1} [{st.session_state.module_unit}]", min_value=0.0, value=float(st.session_state.multi_layers[i]["E"]), step=5.0, key=f"multi_E_{i}")
                else:
                    # GPa affiché – conversion affichage
                    E_gpa = st.session_state.multi_layers[i]["E"] / 1000.0
                    E_gpa = st.number_input(f"E{i+1} [GPa]", min_value=0.0, value=float(E_gpa), step=0.1, key=f"multi_Eg_{i}")
                    st.session_state.multi_layers[i]["E"] = E_gpa * 1000.0
        st.markdown("**Option d'échelle**")
        c1, c2 = st.columns(2)
        with c1:
            apply_scale = st.toggle("Appliquer l'effet de largeur B", value=False, key="multi_scale")
        with c2:
            Bm = st.number_input("B (m)", min_value=0.01, value=2.0, step=0.1, key="multi_B") if apply_scale else None
        if apply_scale:
            nu_m = st.number_input("ν moyen", min_value=0.0, max_value=0.49, value=0.30, step=0.01, key="multi_nu")

    elif cas.startswith("3"):
        st.markdown("**CPT / empirique**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            qt_MPa = st.number_input("q_t (MPa)", min_value=0.0, value=10.0, step=0.5, key="cpt_qt")
        with c2:
            sv0_kPa = st.number_input("σ'v0 (kPa)", min_value=0.0, value=50.0, step=5.0, key="cpt_sv0")
        with c3:
            alphaE = st.number_input("α_E (5–10)", min_value=1.0, value=8.0, step=0.5, key="cpt_alphaE")
        with c4:
            Bc = st.number_input("B (m)", min_value=0.01, value=2.0, step=0.1, key="cpt_B")
        nu_cpt = st.slider("ν (Poisson)", min_value=0.2, max_value=0.45, value=0.30, step=0.01, key="cpt_nu")

    elif cas.startswith("4"):
        st.markdown("**Plat métallique sur béton**")
        c1, c2, c3 = st.columns(3)
        with c1:
            Bp = st.number_input("B plat (mm)", min_value=10.0, value=200.0, step=10.0, key="plate_B")
        with c2:
            Lp = st.number_input("L plat (mm)", min_value=10.0, value=200.0, step=10.0, key="plate_L")
        with c3:
            alpha = st.slider("α (h_c = α·min(B,L))", min_value=0.3, max_value=0.8, value=0.5, step=0.05, key="plate_alpha")
        c4, c5, c6 = st.columns(3)
        with c4:
            Ec = st.number_input("E béton (GPa)", min_value=1.0, value=30.0, step=1.0, key="plate_Ec")
        with c5:
            use_nu = st.toggle("Inclure (1-ν²)?", value=False, key="plate_use_nu")
        with c6:
            nu_c = st.number_input("ν béton", min_value=0.0, max_value=0.49, value=0.20, step=0.01, key="plate_nu")
        st.markdown("**Mortier / résine (option)**")
        c7, c8, c9 = st.columns(3)
        with c7:
            has_grout = st.toggle("Avec mortier/résine", value=True, key="plate_has_grout")
        with c8:
            Eg = st.number_input("E mortier (GPa)", min_value=0.5, value=12.0, step=0.5, key="plate_Eg") if has_grout else 0.0
        with c9:
            tg = st.number_input("t_g (mm)", min_value=0.1, value=10.0, step=0.5, key="plate_tg") if has_grout else 0.0

    elif cas.startswith("5"):
        st.markdown("**Convertisseur & vérification**")
        c1, c2, c3 = st.columns(3)
        with c1:
            p_kg = st.number_input("kg/cm²", min_value=0.0, value=1.0, step=0.1, key="u_kg")
        with c2:
            p_kPa = st.number_input("kPa", min_value=0.0, value=98.0665, step=1.0, key="u_kPa")
        with c3:
            p_MPa = st.number_input("MPa", min_value=0.0, value=0.0980665, step=0.01, key="u_MPa")
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
        with c1:
            q_ctrl = st.number_input("q (kPa)", min_value=0.0, value=100.0, step=10.0, key="u_q")
        with c2:
            k_ctrl = st.number_input("k (MN/m³)", min_value=0.001, value=10.0, step=1.0, key="u_k")
        w_ctrl_mm = (q_ctrl / MNpm3_to_kNpm3(k_ctrl)) * 1000.0  # mm
        st.info(f"w = q/k = **{w_ctrl_mm:.2f} mm**")

    else:  # cas 6 base de connaissances
        st.markdown("**Base de connaissances – Types de sols**")
        st.write("Sélectionnez un type de sol pour voir une description simple et des ordres de grandeur.")
        SOILS = {
            "Argile très molle": {"desc": "Sol très humide, consistance pâteuse, tassements importants.", "E": 8, "ks": (1,3), "qa": (0.1,0.2), "gamma": (16,18)},
            "Argile molle": {"desc": "Cohésive, plasticité marquée, consolidation différée.", "E": 15, "ks": (2,5), "qa": (0.2,0.5), "gamma": (18,19)},
            "Limon meuble": {"desc": "Mélange silt/argile/sable, sensible à l'eau.", "E": 25, "ks": (3,8), "qa": (0.3,0.8), "gamma": (17,19)},
            "Limon compact": {"desc": "Sablo‑limoneux compact, portance moyenne.", "E": 40, "ks": (8,15), "qa": (0.8,1.5), "gamma": (18,20)},
            "Sable meuble": {"desc": "Peu compact, tassements immédiats.", "E": 40, "ks": (8,12), "qa": (0.5,1.0), "gamma": (17,19)},
            "Sable dense": {"desc": "Grains serrés, bon porteur.", "E": 80, "ks": (15,30), "qa": (1.0,2.0), "gamma": (18,20)},
            "Sable graveleux": {"desc": "Très drainant, très bon appui.", "E": 120, "ks": (30,50), "qa": (2.0,3.0), "gamma": (19,21)},
            "Gravier compact": {"desc": "Matériaux grossiers compactés.", "E": 200, "ks": (50,80), "qa": (3.0,5.0), "gamma": (20,22)},
            "Marne / Moraine": {"desc": "Sol calcaire/glaciaire cohérent, rigide.", "E": 300, "ks": (80,150), "qa": (5.0,8.0), "gamma": (21,23)},
            "Roche tendre": {"desc": "Materiau fissuré mais porteur.", "E": 500, "ks": (150,300), "qa": (8.0,15.0), "gamma": (22,24)},
            "Roche dure / Béton": {"desc": "Quasi indéformable.", "E": 1000, "ks": (300,800), "qa": (15.0,30.0), "gamma": (24,27)},
        }
        soil_key = st.selectbox("Type de sol", list(SOILS.keys()), index=5)
        st.session_state.soil_selected = soil_key
        s = SOILS[soil_key]
        st.markdown(f"**Description** : {s['desc']}")
        st.markdown(
            f"**Ordres de grandeur** — E ≈ {s['E']} MPa · k_s ≈ {s['ks'][0]}–{s['ks'][1]} MN/m³ · q_ad ≈ {s['qa'][0]}–{s['qa'][1]} kg/cm² · γ ≈ {s['gamma'][0]}–{s['gamma'][1]} kN/m³"
        )
        st.markdown("\n")
        apply_to = st.selectbox("Envoyer ces valeurs vers…", ["1. Sol homogène (méthode C – E)", "1. Sol homogène (k_s direct)"])
        if st.button("Remplir les champs du cas choisi"):
            if apply_to.startswith("1. Sol homogène (méthode C"):
                st.session_state.page_jump = "1. Sol homogène"
                st.session_state.solo_E = float(s["E"]) if st.session_state.module_unit=="MPa" else float(s["E"]/1000)
                st.success("Valeur E pré-remplie pour le cas 1C.")
            else:
                # on pré-remplit un k_s médian en MN/m³ → converti plus tard côté résultats
                st.session_state.guide_ks = sum(s["ks"]) / 2.0
                st.success("Valeur k_s (guide) stockée – à utiliser dans Sol homogène.")

with col_right:
    st.markdown("### Dimensionnement / Résultats")
    with st.container(border=True):
        # Calculs par cas & affichage
        if cas.startswith("1"):
            method = st.session_state.get("_last_method", None)  # non vital
            # Recalcule selon sélection courante depuis col_left
            method = st.session_state.get("_tmp", None)

        if cas.startswith("1"):
            method_label = st.session_state.get("solo_method", None)
            # On lit le choix directement côté gauche (c'est déjà fait). On recalcule selon A/B/C
            # A. SLS direct
            if 'solo_q' in st.session_state or 'solo_w' in st.session_state:
                pass

            if st.session_state.get("solo_q") is not None and st.session_state.get("solo_w") is not None:
                if st.session_state.get("solo_w") > 0:
                    q_kPa = to_kPa_from(st.session_state.solo_q, st.session_state.press_unit)
                    w_m = st.session_state.solo_w / 1000.0
                    ks_MNpm3 = kNpm3_to_MNpm3(q_kPa / w_m)
                    st.metric("k_s (MN/m³)", f"{ks_MNpm3:,.2f}")
                    st.caption("Méthode A — SLS direct")
                    if st.session_state.show_formulas:
                        latex_left(r"k_s = \dfrac{q}{w}\quad;\quad q\,[\mathrm{kPa}]\; w\,[\mathrm{m}] \Rightarrow k_s\,[\mathrm{kN/m^3}]\,/1000\Rightarrow [\mathrm{MN/m^3}] ")
            # B. q_ad → k_s
            if st.session_state.get("solo_qa") is not None and st.session_state.get("solo_sadm") is not None:
                s_adm_m = st.session_state.solo_sadm / 1000.0
                qa_kPa = to_kPa_from(st.session_state.solo_qa, st.session_state.press_unit)
                qa_used = qa_kPa * (st.session_state.solo_sf if st.session_state.solo_isult else 1.0)
                if s_adm_m > 0:
                    ksB = kNpm3_to_MNpm3(qa_used / s_adm_m)
                    st.metric("k_s (MN/m³)", f"{ksB:,.2f}")
                    st.caption("Méthode B — depuis q_ad")
                    if st.session_state.show_formulas:
                        latex_left(r"k_s = \dfrac{SF\,q_{ad}}{s_{adm}} ")
            # C. depuis E
            if st.session_state.get("solo_E") is not None and st.session_state.get("solo_B") is not None:
                E_input = st.session_state.solo_E
                if st.session_state.module_unit == "GPa":
                    E_MPa = E_input * 1000.0
                else:
                    E_MPa = E_input
                E_kPa = E_MPa_to_kNpm2(E_MPa)
                B = max(st.session_state.solo_B, 1e-6)
                nu = st.session_state.solo_nu
                ksC_kNpm3 = E_kPa / (B * (1 - nu**2))
                ksC = kNpm3_to_MNpm3(ksC_kNpm3)
                st.metric("k_s (MN/m³)", f"{ksC:,.2f}")
                st.caption("Méthode C — depuis E")
                if st.session_state.show_formulas:
                    latex_left(r"k_s = \dfrac{E}{B\,(1-\nu^2)} ")
            # Valeur guide depuis la base de connaissances (si fournie)
            if st.session_state.get("guide_ks"):
                st.info(f"Valeur guide k_s ≈ **{st.session_state.guide_ks:.1f} MN/m³** (Base de connaissances)")

        elif cas.startswith("2"):
            # Série multicouche: k_eq = 1 / sum(h/E)
            layers = st.session_state.multi_layers
            denom = 0.0
            H = 0.0
            for lay in layers:
                h = float(lay['h'])
                H += h
                E = float(lay['E'])  # en MPa
                E_kPa = E_MPa_to_kNpm2(E)
                if E_kPa <= 0:  # évite division par zéro
                    continue
                denom += h / E_kPa
            ks_eq_kNpm3 = (1.0 / denom) if denom > 0 else 0.0
            ks_eq = kNpm3_to_MNpm3(ks_eq_kNpm3)
            st.metric("k_eq (MN/m³)", f"{ks_eq:,.2f}")
            if st.session_state.show_formulas:
                latex_left(r"k_{eq} = \left( \sum_i \dfrac{h_i}{E_i} \right)^{-1}")
            # Option échelle
            if st.session_state.get("multi_scale"):
                Bm = st.session_state.multi_B
                nu_m = st.session_state.multi_nu
                Eeq_kPa = ks_eq_kNpm3 * H  # E_eq = k_eq * H (en kPa)
                ks_scale_kNpm3 = Eeq_kPa / (Bm * (1 - nu_m**2)) if Bm > 0 else 0.0
                ks_scale = kNpm3_to_MNpm3(ks_scale_kNpm3)
                st.metric("k_s avec échelle B (MN/m³)", f"{ks_scale:,.2f}")
                if st.session_state.show_formulas:
                    latex_left(r"E_{eq} = k_{eq}\,H\quad;\quad k_s \approx \dfrac{E_{eq}}{B\,(1-\nu^2)}")

        elif cas.startswith("3"):
            qt_kPa = st.session_state.cpt_qt * 1000.0
            E_kPa = st.session_state.cpt_alphaE * max(qt_kPa - st.session_state.cpt_sv0, 0.0)
            E_MPa = E_kPa / 1000.0
            ks_kNpm3 = E_kPa / (st.session_state.cpt_B * (1 - st.session_state.cpt_nu**2))
            ks = kNpm3_to_MNpm3(ks_kNpm3)
            c1, c2 = st.columns(2)
            c1.metric("E estimé (MPa)", f"{E_MPa:,.1f}")
            c2.metric("k_s (MN/m³)", f"{ks:,.2f}")
            if st.session_state.show_formulas:
                latex_left(r"E = \alpha_E\,(q_t-\sigma'_{v0})\quad;\quad k_s = \dfrac{E}{B\,(1-\nu^2)}")

        elif cas.startswith("4"):
            Bp = st.session_state.plate_B / 1000.0
            Lp = st.session_state.plate_L / 1000.0
            hc = st.session_state.plate_alpha * min(Bp, Lp)
            Ec_kPa = E_GPa_to_kNpm2(st.session_state.plate_Ec)
            if st.session_state.plate_use_nu:
                kc_kNpm3 = Ec_kPa / (hc * (1 - st.session_state.plate_nu**2))
            else:
                kc_kNpm3 = Ec_kPa / hc
            if st.session_state.plate_has_grout and st.session_state.plate_tg > 0:
                Eg_kPa = E_GPa_to_kNpm2(st.session_state.plate_Eg)
                tg_m = st.session_state.plate_tg / 1000.0
                kg_kNpm3 = Eg_kPa / tg_m
                keq_kNpm3 = 1.0 / (1.0/kc_kNpm3 + 1.0/kg_kNpm3)
            else:
                keq_kNpm3 = kc_kNpm3
            keq = kNpm3_to_MNpm3(keq_kNpm3)
            c1, c2, c3 = st.columns(3)
            c1.metric("h_c (m)", f"{hc:,.3f}")
            c2.metric("k_c (MN/m³)", f"{kNpm3_to_MNpm3(kc_kNpm3):,.1f}")
            c3.metric("k_eq (MN/m³)", f"{keq:,.1f}")
            if st.session_state.show_formulas:
                latex_left(r"k_c = \dfrac{E_c}{h_c}\quad;\quad k_g = \dfrac{E_g}{t_g}\quad;\quad \dfrac{1}{k_{eq}} = \dfrac{1}{k_c} + \dfrac{1}{k_g}")

        elif cas.startswith("5"):
            st.info("Utilisez les boutons de synchronisation côté gauche pour convertir les unités. Le contrôle q→w est affiché à gauche.")

        else:  # base de connaissances
            st.warning("Choisissez un type de sol à gauche. Utilisez le bouton pour pré-remplir un cas.")

    # ----------
    # Notes
    # ----------
    with st.expander("Notes & rappels"):
        st.write("""
- Dans SCIA, la raideur de support pour une plaque se saisit en **MN/m³** (k = k_s).
- Méthode **A (SLS direct)** est à privilégier lorsqu'un tableau q–w (tassements) est fourni par l'étude géotechnique.
- Méthode **B** convertit une contrainte admissible et un tassement admissible en raideur équivalente.
- Méthode **C** est utile quand on dispose d'un module E (ou d'un CPT → E) ; pensez à l'effet d'échelle **B**.
- Pour un **plat sur béton**, modélisez l'appui local via les couches en série (béton + mortier de calage).
        """)


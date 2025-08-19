# modules/garde_corps.py
import math
import streamlit as st

E_STEEL = 210000.0  # MPa
GAMMA_M0 = 1.0      # EC3 (à ajuster si besoin)
DEFAULT_FY = 235.0  # MPa

# -----------------------------
# PROPRIÉTÉS DE SECTION
def I_W_rect(b_mm, h_mm):
    """Plein rectangle, flexion autour axe passant par la largeur b (h = hauteur dans le plan de flexion)"""
    I = b_mm * h_mm**3 / 12.0
    W = I / (h_mm / 2.0)
    return I, W

def I_W_RHS(b_mm, h_mm, t_mm):
    """Tube rectangulaire (RHS) – b = largeur, h = hauteur dans le plan de flexion"""
    bi = max(b_mm - 2*t_mm, 1e-6)
    hi = max(h_mm - 2*t_mm, 1e-6)
    I = (b_mm*h_mm**3 - bi*hi**3) / 12.0
    W = I / (h_mm/2.0)
    return I, W

def I_W_CHS(D_mm, t_mm):
    """Tube circulaire (CHS)"""
    Do = D_mm
    Di = max(D_mm - 2*t_mm, 1e-6)
    I = (math.pi/64.0) * (Do**4 - Di**4)
    W = I / (Do/2.0)
    return I, W

# petites listes standard (à compléter à volonté)
STD_RHS = ["40x40x3", "50x50x3", "60x40x3", "60x60x3", "80x40x3", "80x40x4", "80x80x4"]
def parse_rhs(tag):
    b, h, t = tag.split("x")
    return float(b), float(h), float(t)

STD_CHS = ["Ø33.7x2.6", "Ø42.4x2.6", "Ø48.3x3.2", "Ø60.3x3.2"]
def parse_chs(tag):
    tag = tag.replace("Ø", "")
    D, t = tag.split("x")
    return float(D), float(t)

# -----------------------------
# OUTILS DE CALCUL
def post_cantilever_results(H_mm, q_kNm_line, Q_kN, s_m, I_mm4, W_mm3, E_MPa):
    """
    Montant encastré de hauteur H, soumis en tête :
      - à un effort horizontal équivalent P = max(q*s, Q)
      - flèche sous P (ELS) : d = P*H^3/(3 E I)
    """
    P_kN = max(q_kNm_line * s_m, Q_kN)
    M_kNm = P_kN * (H_mm/1000.0)
    V_kN = P_kN

    sigma_MPa = (M_kNm * 1e6) / W_mm3          # N/mm²
    d_mm = (P_kN*1000.0) * (H_mm**3) / (3.0 * E_MPa * I_mm4)

    return {
        "P_kN": P_kN, "M_kNm": M_kNm, "V_kN": V_kN,
        "sigma_MPa": sigma_MPa, "d_mm": d_mm
    }

def handrail_beam_results(s_m, q_kNm_line, Q_kN, I_mm4, W_mm3, E_MPa):
    """
    Main courante entre montants espacés de s :
      - cas poutre simplement appuyée (conservatif)
      - Mmax sous q : q*s²/8 ; sous Q centré : Q*s/4 (on prend le pire et on cumule si besoin)
      - flèche sous q : 5 q L^4 / (384 E I) ; sous Q : Q L^3 / (48 E I)
    """
    L_m = s_m
    Mq = q_kNm_line * L_m**2 / 8.0
    MQ = Q_kN * L_m / 4.0
    M_kNm = max(Mq, MQ)

    dq_mm = (5 * (q_kNm_line*1000.0) * (L_m*1000.0)**4) / (384.0 * E_MPa * I_mm4)
    dQ_mm = ((Q_kN*1000.0) * (L_m*1000.0)**3) / (48.0 * E_MPa * I_mm4)
    d_mm = dq_mm + dQ_mm
    sigma_MPa = (M_kNm * 1e6) / W_mm3
    V_kN = q_kNm_line * L_m / 2.0 + Q_kN / 2.0
    return {"M_kNm": M_kNm, "V_kN": V_kN, "sigma_MPa": sigma_MPa, "d_mm": d_mm}

def infill_bar_results(L_mm, q_panel_kNm2, spacing_mm, I_mm4, W_mm3, E_MPa, orientation="vertical"):
    """
    Montant intermédiaire (barreau) entre lisses :
      - charge surfacique sur le panneau (kN/m²) -> charge linéique sur le barreau q_bar (kN/m)
      - barreau simplement appuyé
    """
    q_bar_kNm = q_panel_kNm2 * (spacing_mm/1000.0 if orientation=="vertical" else L_mm/1000.0)
    L_m = L_mm/1000.0
    M_kNm = q_bar_kNm * L_m**2 / 8.0
    d_mm = (5 * (q_bar_kNm*1000.0) * (L_m*1000.0)**4) / (384.0 * E_MPa * I_mm4)
    sigma_MPa = (M_kNm * 1e6) / W_mm3
    return {"q_bar_kNm": q_bar_kNm, "M_kNm": M_kNm, "sigma_MPa": sigma_MPa, "d_mm": d_mm}

# -----------------------------
# WELD CHECK (simplifiée – cordon d’angle tout autour)
def weld_ring_utilisation(D_or_perim_mm, a_throat_mm, V_kN, M_kNm, shape="CHS", fy_weld_MPa=360.0):
    """
    Vérif simplifiée du cordon périphérique:
    - Résistance nominale au cisaillement ~ 0.8 * f_u (ici on prend fy_weld_MPa en MPa pour ordre)
    - Répartition: cisaillement direct + torsion de St Venant sur le groupe de soudure
      Approche simplifiée CHS: J ≈ 2πR * a * R^2 = 2π a R^3 ; tau_max = M*1e6 * R / J
    - Pour RHS (périmètre P), on approxime J ≈ P * a * (r_eq)^2 avec r_eq ≈ min(b,h)/2
    """
    if shape == "CHS":
        R = D_or_perim_mm/2.0
        J = 2.0 * math.pi * a_throat_mm * (R**3)
        r_max = R
        P = 2.0 * math.pi * R
    else:
        P = D_or_perim_mm      # ici on passe le périmètre total soudé
        r_max = D_or_perim_mm/8.0  # approx r_eq ~ min(b,h)/2 ~ P/8 pour un rectangle carré
        J = P * a_throat_mm * (r_max**2)

    tau_dir = (V_kN*1000.0) / (P * a_throat_mm)
    tau_mom = (M_kNm*1e6) * r_max / max(J, 1e-6)
    tau_comb = math.hypot(tau_dir, tau_mom)  # combinaison quadratique

    Rk = 0.6 * fy_weld_MPa  # résistance de calcul simplifiée (≈ 0.6 fu)
    util = tau_comb / Rk
    return {"tau_dir": tau_dir, "tau_mom": tau_mom, "tau_comb": tau_comb, "util": util}

# -----------------------------
def show():
    st.header("Dimensionnement d’un **garde-corps**")

    left, right = st.columns([1, 1.2])

    with left:
        st.subheader("1) Hypothèses générales")
        H = st.number_input("Hauteur du garde-corps H (mm)", 900.0, 1300.0, 1100.0, step=10.0)
        s = st.number_input("Entraxe des montants principaux s (mm)", 400.0, 2000.0, 1000.0, step=50.0)  # mm
        fy = st.number_input("Acier fy (MPa)", 235.0, 460.0, DEFAULT_FY, step=5.0)
        gamma_M0 = st.number_input("γM0", 1.0, 1.2, GAMMA_M0, step=0.05)

        st.markdown("**Charges normatives (paramétrables)**")
        preset = st.selectbox(
            "Type d’usage (préset)",
            ["Résidentiel (0.5 kN/m)", "Bureaux (1.0 kN/m)", "Lieux publics (3.0 kN/m)", "Personnalisé"]
        )
        if preset == "Résidentiel (0.5 kN/m)":
            q_line = 0.5
            Q_point = 1.0
        elif preset == "Bureaux (1.0 kN/m)":
            q_line = 1.0
            Q_point = 1.0
        elif preset == "Lieux publics (3.0 kN/m)":
            q_line = 3.0
            Q_point = 1.5
        else:
            q_line = st.number_input("Charge linéaire horizontale q (kN/m)", 0.1, 5.0, 1.0, step=0.1)
            Q_point = st.number_input("Charge ponctuelle en tête Q (kN)", 0.1, 3.0, 1.0, step=0.1)

        st.caption("⚠️ Ajuste ces valeurs selon ton **Annexe Nationale**.")

        st.subheader("2) Montant principal")
        typ_montant = st.radio("Type de section", ["RHS", "CHS", "Rectangulaire pleine"], horizontal=True)
        use_std_p = st.toggle("Section **standard**", value=True, key="std_p")

        if typ_montant == "RHS":
            if use_std_p:
                tag = st.selectbox("RHS standard (b×h×t mm)", STD_RHS, key="rhs_p")
                b, h, t = parse_rhs(tag)
            else:
                b = st.number_input("b (mm)", 20.0, 200.0, 50.0, step=1.0, key="b_p")
                h = st.number_input("h (mm)", 20.0, 200.0, 50.0, step=1.0, key="h_p")
                t = st.number_input("t (mm)", 2.0, 12.0, 3.0, step=0.1, key="t_p")
            I_post, W_post = I_W_RHS(b, h, t)

        elif typ_montant == "CHS":
            if use_std_p:
                tag = st.selectbox("CHS standard (Ø×t mm)", STD_CHS, key="chs_p")
                D, t = parse_chs(tag)
            else:
                D = st.number_input("D (mm)", 21.3, 168.3, 48.3, step=0.1, key="D_p")
                t = st.number_input("t (mm)", 2.0, 10.0, 3.2, step=0.1, key="t_chs_p")
            I_post, W_post = I_W_CHS(D, t)

        else:
            b = st.number_input("Largeur b (mm)", 5.0, 100.0, 40.0, step=1.0, key="b_rect_p")
            h = st.number_input("Hauteur h (mm)", 5.0, 120.0, 8.0, step=1.0, key="h_rect_p")
            I_post, W_post = I_W_rect(b, h)

        st.subheader("3) Main courante")
        typ_mc = st.radio("Type de section", ["RHS", "CHS", "Rectangulaire pleine"], horizontal=True, key="mc_type")
        use_std_mc = st.toggle("Section **standard**", value=True, key="std_mc")

        if typ_mc == "RHS":
            if use_std_mc:
                tag = st.selectbox("RHS standard", STD_RHS, key="rhs_mc")
                bmc, hmc, tmc = parse_rhs(tag)
            else:
                bmc = st.number_input("b (mm)", 20.0, 200.0, 40.0, step=1.0, key="b_mc")
                hmc = st.number_input("h (mm)", 20.0, 200.0, 20.0, step=1.0, key="h_mc")
                tmc = st.number_input("t (mm)", 2.0, 12.0, 3.0, step=0.1, key="t_mc")
            I_mc, W_mc = I_W_RHS(bmc, hmc, tmc)

        elif typ_mc == "CHS":
            if use_std_mc:
                tag = st.selectbox("CHS standard", STD_CHS, key="chs_mc")
                Dmc, tmc = parse_chs(tag)
            else:
                Dmc = st.number_input("D (mm)", 21.3, 168.3, 42.4, step=0.1, key="D_mc")
                tmc = st.number_input("t (mm)", 2.0, 10.0, 2.6, step=0.1, key="t_chs_mc")
            I_mc, W_mc = I_W_CHS(Dmc, tmc)

        else:
            bmc = st.number_input("b (mm)", 5.0, 100.0, 40.0, step=1.0, key="b_rect_mc")
            hmc = st.number_input("h (mm)", 5.0, 120.0, 8.0, step=1.0, key="h_rect_mc")
            I_mc, W_mc = I_W_rect(bmc, hmc)

        st.subheader("4) Montants intermédiaires (barreaux)")
        orientation = st.radio("Orientation", ["vertical", "horizontal"], horizontal=True)
        L_bar = st.number_input("Portée du barreau L (mm)", 100.0, 2000.0, 900.0, step=10.0)
        spacing = st.number_input("Entraxe des barreaux (mm)", 50.0, 200.0, 110.0, step=5.0)
        q_panel = st.number_input("Charge sur panneau (kN/m²)", 0.2, 5.0, 1.0, step=0.1)

        typ_bar = st.radio("Section barreau", ["RHS", "CHS", "Rectangulaire pleine"], horizontal=True, key="bar_type")
        if typ_bar == "RHS":
            tag = st.selectbox("RHS standard", STD_RHS, key="rhs_bar")
            bb, hb, tb = parse_rhs(tag)
            I_bar, W_bar = I_W_RHS(bb, hb, tb)
        elif typ_bar == "CHS":
            tag = st.selectbox("CHS standard", STD_CHS, key="chs_bar")
            Db, tb = parse_chs(tag)
            I_bar, W_bar = I_W_CHS(Db, tb)
        else:
            bb = st.number_input("b (mm)", 5.0, 80.0, 20.0, step=1.0, key="b_rect_bar")
            hb = st.number_input("h (mm)", 5.0, 80.0, 6.0, step=1.0, key="h_rect_bar")
            I_bar, W_bar = I_W_rect(bb, hb)

        st.subheader("5) Critères ELS/ELU")
        d_lim_post = st.number_input("Flèche max en tête montant (mm)", 5.0, 50.0, 20.0, step=1.0)
        d_lim_mc = st.number_input("Flèche max main courante (mm)", 5.0, 30.0, 15.0, step=1.0)

        check_weld = st.toggle("🔧 Vérifier la **soudure** montant/platine", value=False)
        if check_weld:
            st.markdown("**Hypothèses soudure (tout-autour)**")
            if typ_montant == "CHS":
                Dwp = st.number_input("Diamètre extérieur du tube (mm)", 21.3, 168.3, D if "D" in locals() else 48.3, step=0.1)
                perim = math.pi * Dwp
                shape = "CHS"
                scalar = Dwp
            elif typ_montant == "RHS":
                bwp = st.number_input("Périmètre soudé total P (mm)", 100.0, 2000.0, 4*(b+h) if "b" in locals() else 400.0, step=10.0)
                perim = bwp
                shape = "RHS"
                scalar = bwp
            else:
                bwp = st.number_input("Périmètre soudé total P (mm)", 100.0, 2000.0, 200.0, step=10.0)
                perim = bwp
                shape = "RHS"
                scalar = bwp
            a_throat = st.number_input("Gorge efficace a (mm)", 2.0, 10.0, 4.0, step=0.5)

    # -----------------------------
    # CALCULS
    s_m = s/1000.0
    # Montant
    res_post = post_cantilever_results(H, q_line, Q_point, s_m, I_post, W_post, E_STEEL)
    # Main courante
    res_mc = handrail_beam_results(s_m, q_line, Q_point, I_mc, W_mc, E_STEEL)
    # Barreaux
    res_bar = infill_bar_results(L_bar, q_panel, spacing, I_bar, W_bar, E_STEEL, orientation=orientation)

    # Résistances ELU acier (section élastique – conservative)
    sigma_Rd = fy / gamma_M0

    # -----------------------------
    # AFFICHAGE
    with right:
        st.subheader("Synthèse dimensionnement")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("q (kN/m)", f"{q_line:.2f}")
        c2.metric("Q (kN)", f"{Q_point:.2f}")
        c3.metric("H (mm)", f"{H:.0f}")
        c4.metric("Entraxe s (mm)", f"{s:.0f}")

        st.divider()
        st.markdown("### Montant principal (encastré)")
        st.write(f"- **P** = {res_post['P_kN']:.2f} kN ; **M** = {res_post['M_kNm']:.2f} kN·m ; **V** = {res_post['V_kN']:.2f} kN")
        st.write(f"- **σ** = {res_post['sigma_MPa']:.1f} MPa  → utilisation ELU = {100*res_post['sigma_MPa']/sigma_Rd:.0f}%")
        st.write(f"- **Flèche en tête** d = {res_post['d_mm']:.1f} mm (limite {d_lim_post:.1f} mm) "
                 f"{'✅' if res_post['d_mm']<=d_lim_post else '❌'}")
        st.progress(min(res_post['sigma_MPa']/sigma_Rd,1.0))

        st.markdown("### Main courante (poutre simplement appuyée)")
        st.write(f"- **M** = {res_mc['M_kNm']:.2f} kN·m ; **V** = {res_mc['V_kN']:.2f} kN")
        st.write(f"- **σ** = {res_mc['sigma_MPa']:.1f} MPa  → utilisation ELU = {100*res_mc['sigma_MPa']/sigma_Rd:.0f}%")
        st.write(f"- **Flèche** d = {res_mc['d_mm']:.1f} mm (limite {d_lim_mc:.1f} mm) "
                 f"{'✅' if res_mc['d_mm']<=d_lim_mc else '❌'}")
        st.progress(min(res_mc['sigma_MPa']/sigma_Rd,1.0))

        st.markdown("### Barreaux (intermédiaires)")
        st.write(f"- q_bar = {res_bar['q_bar_kNm']:.2f} kN/m ; **M** = {res_bar['M_kNm']:.3f} kN·m")
        st.write(f"- **σ** = {res_bar['sigma_MPa']:.1f} MPa  → utilisation ELU = {100*res_bar['sigma_MPa']/sigma_Rd:.0f}%")
        st.write(f"- **Flèche** d = {res_bar['d_mm']:.1f} mm")
        st.progress(min(res_bar['sigma_MPa']/sigma_Rd,1.0))

        if check_weld:
            st.markdown("### 🔧 Soudure montant / platine (simplifiée)")
            weld = weld_ring_utilisation(
                D_or_perim_mm=scalar, a_throat_mm=a_throat,
                V_kN=res_post["V_kN"], M_kNm=res_post["M_kNm"], shape=("CHS" if shape=="CHS" else "RHS")
            )
            st.write(f"- **τ_dir** = {weld['tau_dir']:.1f} MPa ; **τ_mom** = {weld['tau_mom']:.1f} MPa")
            st.write(f"- **τ_comb** = {weld['tau_comb']:.1f} MPa ; **taux** = {100*weld['util']:.0f}% "
                     f"{'✅' if weld['util']<=1.0 else '❌'}")
            st.caption("Approche simplifiée pour un premier dimensionnement ; à affiner selon EC3 et détails de platine/ANC.")

        st.divider()
        st.markdown("#### Hypothèses")
        st.caption(
            "- Répartition conservatrice : chaque **montant** reprend `max(q·s, Q)` appliqué en tête.\n"
            "- **Main courante** : poutre simplement appuyée entre montants (tu peux raffiner en **encastré/continu** si besoin).\n"
            "- **Barreaux** : charge de panneau convertie en charge de ligne sur un barreau simplement appuyé.\n"
            "- Résistance ELU basée sur la **contrainte de flexion** σ ≤ fy/γM0 (section élastique).\n"
            "- Soudure : vérif périphérique **simplifiée** (cordon tout-autour)."
        )

# modules/garde_corps.py
import math
import streamlit as st

E_STEEL = 210000.0  # MPa

# ------- sections
STD_RHS = ["400x40x3", "50x50x3", "60x40x3", "60x60x3", "80x40x3", "80x40x4", "80x80x4"]
STD_CHS = ["Ø33.7x2.6", "Ø42.4x2.6", "Ø48.3x3.2", "Ø60.3x3.2"]

def parse_rhs(tag): b,h,t = tag.split("x"); return float(b),float(h),float(t)
def parse_chs(tag): D,t = tag.replace("Ø","").split("x"); return float(D),float(t)

def I_W_rect(b, h):
    I = b*h**3/12.0; W = I/(h/2.0); return I, W
def I_W_RHS(b, h, t):
    bi, hi = max(b-2*t,1e-6), max(h-2*t,1e-6)
    I = (b*h**3 - bi*hi**3)/12.0; W = I/(h/2.0); return I, W
def I_W_CHS(D, t):
    Do, Di = D, max(D-2*t,1e-6)
    I = (math.pi/64.0)*(Do**4 - Di**4); W = I/(Do/2.0); return I, W

def shear_area_rect(b,h): return b*h
def shear_area_rhs(b,h,t): return 2*t*(b+h)         # approx mince
def shear_area_chs(D,t):   return math.pi*D*t       # mince

def defl_cantilever_tip(P_kN, H_mm, E, I):  # mm
    return (P_kN*1000.0)*(H_mm**3)/(3.0*E*I)
def defl_simple_q(q_kN_m, L_m, E, I):       # mm
    return (5.0*(q_kN_m*1000.0)*(L_m*1000.0)**4)/(384.0*E*I)
def defl_simple_Pmid(P_kN, L_m, E, I):      # mm
    return ((P_kN*1000.0)*(L_m*1000.0)**3)/(48.0*E*I)

def lim_fleche_mm(L_mm, mode, val):
    if mode == "L/x":
        x = max(float(val), 1.0)
        return L_mm/x
    return float(val)

def box_ok(ok, txt):
    (st.success if ok else st.error)(txt)

def show():
    st.markdown("## Garde-corps")

    left, right = st.columns([1, 1.25])

    # -------------------- Entrées (colonne gauche)
    with left:
        st.markdown("### Informations")
        c1,c2 = st.columns(2)
        with c1:
            H = st.number_input("Hauteur utile (mm)", 800.0, 1400.0, 1100.0, step=10.0)
        with c2:
            s = st.number_input("Entraxe montants s (mm)", 400.0, 2500.0, 1000.0, step=50.0)

        st.markdown("### Charges (ELS)")
        c1,c2,c3 = st.columns(3)
        with c1:
            charge_mode = st.radio("Charge montant", ["P directe", "à partir de q×s"], horizontal=True)
        with c2:
            P_dir = st.number_input("P (kN)", 0.0, 10.0, 1.0, step=0.1, disabled=(charge_mode!="P directe"))
        with c3:
            q_line = st.number_input("q (kN/m)", 0.0, 5.0, 1.0, step=0.1, disabled=(charge_mode!="à partir de q×s"))

        c1,c2,c3 = st.columns(3)
        with c1:
            Q_point = st.number_input("Q ponctuelle main courante (kN)", 0.0, 5.0, 0.0, step=0.1)
        with c2:
            comb_mc = st.radio("Combinaison main courante", ["max", "somme"], horizontal=True)
        with c3:
            E_mod = st.number_input("E acier (MPa)", 100000.0, 220000.0, E_STEEL, step=1000.0)

        st.markdown("### Matériau & limites")
        c1,c2 = st.columns(2)
        with c1:
            sigma_adm = st.number_input("σ admissible (MPa)", 50.0, 300.0, 160.0, step=5.0)
        with c2:
            tau_adm   = st.number_input("τ admissible (MPa)", 10.0, 200.0, 90.0, step=5.0)

        st.markdown("### Montant principal – section")
        mod_montant = st.radio("Modèle", ["Encastré (charge en tête)", "Poutre simple (charge à mi-portée)"], horizontal=False)
        typ_p = st.radio("Type", ["RHS","CHS","Rectangulaire"], horizontal=True, key="p_type")
        use_std_p = st.toggle("Section standard", value=True, key="p_std")

        if typ_p=="RHS":
            if use_std_p:
                tag = st.selectbox("RHS (b×h×t)", STD_RHS, key="p_rhs")
                bp,hp,tp = parse_rhs(tag)
            else:
                bp = st.number_input("b (mm)", 20.0, 200.0, 50.0, step=1.0, key="bp")
                hp = st.number_input("h (mm)", 20.0, 200.0, 50.0, step=1.0, key="hp")
                tp = st.number_input("t (mm)", 2.0, 12.0, 3.0, step=0.1, key="tp")
            I_post, W_post = I_W_RHS(bp,hp,tp); Av_post = shear_area_rhs(bp,hp,tp)
        elif typ_p=="CHS":
            if use_std_p:
                tag = st.selectbox("CHS (Ø×t)", STD_CHS, key="p_chs")
                Dp,tp = parse_chs(tag)
            else:
                Dp = st.number_input("D (mm)", 21.3, 168.3, 48.3, step=0.1, key="Dp")
                tp = st.number_input("t (mm)", 2.0, 10.0, 3.2, step=0.1, key="tp2")
            I_post, W_post = I_W_CHS(Dp,tp); Av_post = shear_area_chs(Dp,tp)
        else:
            bp = st.number_input("b (mm)", 5.0, 120.0, 40.0, step=1.0, key="bp_rect")
            hp = st.number_input("h (mm)", 5.0, 200.0, 8.0, step=1.0, key="hp_rect")
            I_post, W_post = I_W_rect(bp,hp); Av_post = shear_area_rect(bp,hp)

        st.markdown("### Main courante – section")
        typ_mc = st.radio("Type", ["RHS","CHS","Rectangulaire"], horizontal=True, key="mc_type")
        use_std_mc = st.toggle("Section standard", value=True, key="mc_std")

        if typ_mc=="RHS":
            if use_std_mc:
                tag = st.selectbox("RHS (b×h×t)", STD_RHS, key="mc_rhs")
                bmc,hmc,tmc = parse_rhs(tag)
            else:
                bmc = st.number_input("b (mm)", 20.0, 200.0, 40.0, step=1.0, key="bmc")
                hmc = st.number_input("h (mm)", 20.0, 200.0, 20.0, step=1.0, key="hmc")
                tmc = st.number_input("t (mm)", 2.0, 12.0, 3.0, step=0.1, key="tmc")
            I_mc, W_mc = I_W_RHS(bmc,hmc,tmc); Av_mc = shear_area_rhs(bmc,hmc,tmc)
        elif typ_mc=="CHS":
            if use_std_mc:
                tag = st.selectbox("CHS (Ø×t)", STD_CHS, key="mc_chs")
                Dmc,tmc = parse_chs(tag)
            else:
                Dmc = st.number_input("D (mm)", 21.3, 168.3, 42.4, step=0.1, key="Dmc")
                tmc = st.number_input("t (mm)", 2.0, 10.0, 2.6, step=0.1, key="tmc2")
            I_mc, W_mc = I_W_CHS(Dmc,tmc); Av_mc = shear_area_chs(Dmc,tmc)
        else:
            bmc = st.number_input("b (mm)", 5.0, 120.0, 40.0, step=1.0, key="bmc_rect")
            hmc = st.number_input("h (mm)", 5.0, 200.0, 8.0, step=1.0, key="hmc_rect")
            I_mc, W_mc = I_W_rect(bmc,hmc); Av_mc = shear_area_rect(bmc,hmc)

        st.markdown("### Limites de flèche")
        c1,c2 = st.columns(2)
        with c1:
            mode_post = st.radio("Montant", ["L/x","mm"], horizontal=True, key="lim_post_mode")
            val_post  = st.number_input("Valeur", 1.0, 1000.0, 200.0, step=5.0, key="lim_post_val")
        with c2:
            mode_mc = st.radio("Main courante", ["L/x","mm"], horizontal=True, key="lim_mc_mode")
            val_mc  = st.number_input("Valeur ", 1.0, 1000.0, 200.0, step=5.0, key="lim_mc_val")

    # -------------------- Calculs
    s_m = s/1000.0
    H_m = H/1000.0

    # Charge sur montant
    P_montant = P_dir if charge_mode=="P directe" else q_line * s_m

    # Montant – efforts / contraintes / flèche
    if "Encastré" in mod_montant:
        M_post = P_montant * H_m
        V_post = P_montant
        d_post = defl_cantilever_tip(P_montant, H, E_mod, I_post)
    else:
        # poutre simple L = H, charge à mi-portée
        M_post = P_montant * H_m / 4.0
        V_post = P_montant / 2.0
        d_post = defl_simple_Pmid(P_montant, H_m, E_mod, I_post)

    sigma_post = (M_post * 1e6) / W_post
    tau_post   = (V_post * 1000.0) / Av_post
    lim_post_mm = lim_fleche_mm(H, mode_post, val_post)

    # Main courante
    L_mc = s_m
    Mq = q_line * L_mc**2 / 8.0
    MQ = Q_point * L_mc / 4.0
    if comb_mc == "max":
        M_mc = max(Mq, MQ)
        d_mc = max(defl_simple_q(q_line, L_mc, E_mod, I_mc),
                   defl_simple_Pmid(Q_point, L_mc, E_mod, I_mc))
        V_mc = max(q_line*L_mc/2.0, Q_point/2.0)
    else:
        M_mc = Mq + MQ
        d_mc = defl_simple_q(q_line, L_mc, E_mod, I_mc) + defl_simple_Pmid(Q_point, L_mc, E_mod, I_mc)
        V_mc = q_line*L_mc/2.0 + Q_point/2.0

    sigma_mc = (M_mc * 1e6) / W_mc
    tau_mc   = (V_mc * 1000.0) / Av_mc
    lim_mc_mm = lim_fleche_mm(s, mode_mc, val_mc)

    # -------------------- Résultats (colonne droite)
    with right:
        st.markdown("### Dimensionnement")

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("H (mm)", f"{H:.0f}")
        c2.metric("s (mm)", f"{s:.0f}")
        c3.metric("q (kN/m)", f"{q_line:.2f}")
        c4.metric("Q (kN)", f"{Q_point:.2f}")

        # ---- Montant
        st.markdown("#### Montant principal")
        st.write(f"**P** = {P_montant:.2f} kN  |  **M** = {M_post:.3f} kN·m  |  **V** = {V_post:.3f} kN")
        ok_sigma_p = sigma_post <= sigma_adm
        ok_tau_p   = tau_post   <= tau_adm
        ok_def_p   = d_post     <= lim_post_mm
        box_ok(ok_sigma_p, f"Contrainte σ = {sigma_post:.1f} MPa ≤ {sigma_adm:.1f} MPa")
        box_ok(ok_tau_p,   f"Cisaillement τ = {tau_post:.1f} MPa ≤ {tau_adm:.1f} MPa")
        box_ok(ok_def_p,   f"Flèche d = {d_post:.1f} mm ≤ {lim_post_mm:.1f} mm")

        st.divider()

        # ---- Main courante
        st.markdown("#### Main courante")
        st.write(f"**M** = {M_mc:.3f} kN·m  |  **V** = {V_mc:.3f} kN")
        ok_sigma_mc = sigma_mc <= sigma_adm
        ok_tau_mc   = tau_mc   <= tau_adm
        ok_def_mc   = d_mc     <= lim_mc_mm
        box_ok(ok_sigma_mc, f"Contrainte σ = {sigma_mc:.1f} MPa ≤ {sigma_adm:.1f} MPa")
        box_ok(ok_tau_mc,   f"Cisaillement τ = {tau_mc:.1f} MPa ≤ {tau_adm:.1f} MPa")
        box_ok(ok_def_mc,   f"Flèche d = {d_mc:.1f} mm ≤ {lim_mc_mm:.1f} mm")

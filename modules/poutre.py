# === Vérification de l'effort tranchant standard ===

if V > 0:
    st.markdown("### ⚙️ Vérification de l'effort tranchant (normal)")
    
    tau = V * 1e3 / (0.75 * b * h * 100)
    tau_1 = 0.016 * fck_cube / 1.05
    tau_2 = 0.032 * fck_cube / 1.05
    tau_4 = 0.064 * fck_cube / 1.05

    if tau <= tau_1:
        besoin = "Pas besoin d’étriers"
        icone = "✅"
        tau_lim_aff = tau_1
        nom_lim = "τ_adm_I"
    elif tau <= tau_2:
        besoin = "Besoin d’étriers"
        icone = "✅"
        tau_lim_aff = tau_2
        nom_lim = "τ_adm_II"
    elif tau <= tau_4:
        besoin = "Besoin de barres inclinées et d’étriers"
        icone = "⚠️"
        tau_lim_aff = tau_4
        nom_lim = "τ_adm_IV"
    else:
        besoin = "Pas acceptable"
        icone = "❌"
        tau_lim_aff = tau_4
        nom_lim = "τ_adm_IV"

    st.markdown(f"**τ = {tau:.2f} N/mm² ≤ {nom_lim} = {tau_lim_aff:.2f} N/mm² → {besoin} {icone}**")

    st.markdown("⚙️ Détermination des étriers")
    Ast_etrier = st.session_state.get("n_etriers", 2) * math.pi * (st.session_state.get("ø_etrier", 16) / 2) ** 2
    pas_theorique = Ast_etrier * (int(fyk) / 1.5) * d * 10 / (10 * V * 1e3)
    st.markdown(f"**Pas théorique = {pas_theorique:.1f} cm**")

    col1, col2, col3 = st.columns(3)
    with col1:
        n_etriers = st.selectbox("Nbr. étriers", list(range(1, 5)), key="n_etriers")
    with col2:
        d_etrier = st.selectbox("Ø étriers (mm)", [6, 8, 10], key="ø_etrier")
    with col3:
        pas_choisi = st.number_input("Pas choisi (cm)", min_value=5.0, max_value=50.0, step=0.5, key="pas_etrier")

    Ast_etrier = n_etriers * math.pi * (d_etrier / 2) ** 2
    pas_theorique = Ast_etrier * (int(fyk) / 1.5) * d * 10 / (10 * V * 1e3)

    if pas_choisi <= pas_theorique:
        icone_pas = "✅"
    elif pas_choisi <= 30:
        icone_pas = "⚠️"
    else:
        icone_pas = "❌"

    st.markdown(f"**→ Pas choisi = {pas_choisi:.1f} cm {icone_pas}**")
else:
    st.info("⚠️ L'effort tranchant V est nul → vérification des étriers ignorée.")


# === Vérification de l'effort tranchant réduit (optionnel) ===

if v_sup and V_lim > 0:
    st.markdown("### ⚙️ Vérification de l'effort tranchant réduit")
    
    tau_r = V_lim * 1e3 / (0.75 * b * h * 100)

    if tau_r <= tau_1:
        besoin_r = "Pas besoin d’étriers"
        icone_r = "✅"
        tau_lim_aff_r = tau_1
        nom_lim_r = "τ_adm_I"
    elif tau_r <= tau_2:
        besoin_r = "Besoin d’étriers"
        icone_r = "✅"
        tau_lim_aff_r = tau_2
        nom_lim_r = "τ_adm_II"
    elif tau_r <= tau_4:
        besoin_r = "Besoin de barres inclinées et d’étriers"
        icone_r = "⚠️"
        tau_lim_aff_r = tau_4
        nom_lim_r = "τ_adm_IV"
    else:
        besoin_r = "Pas acceptable"
        icone_r = "❌"
        tau_lim_aff_r = tau_4
        nom_lim_r = "τ_adm_IV"

    st.markdown(f"**τ = {tau_r:.2f} N/mm² ≤ {nom_lim_r} = {tau_lim_aff_r:.2f} N/mm² → {besoin_r} {icone_r}**")

    st.markdown("⚙️ Détermination des étriers réduits")
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        n_etriers_r = st.selectbox("Nbr. étriers (réduit)", list(range(1, 5)), key="n_etriers_r")
    with col_r2:
        d_etrier_r = st.selectbox("Ø étriers (mm) (réduit)", [6, 8, 10], key="ø_etrier_r")
    with col_r3:
        pas_choisi_r = st.number_input("Pas choisi (cm) (réduit)", min_value=5.0, max_value=50.0, step=0.5, key="pas_etrier_r")

    Ast_etrier_r = n_etriers_r * math.pi * (d_etrier_r / 2) ** 2
    pas_theorique_r = Ast_etrier_r * (int(fyk) / 1.5) * d * 10 / (10 * V_lim * 1e3)
    st.markdown(f"**Pas théorique (réduit) = {pas_theorique_r:.1f} cm**")

    if pas_choisi_r <= pas_theorique_r:
        icone_pas_r = "✅"
    elif pas_choisi_r <= 30:
        icone_pas_r = "⚠️"
    else:
        icone_pas_r = "❌"

    st.markdown(f"**→ Pas choisi = {pas_choisi_r:.1f} cm {icone_pas_r}**")
elif v_sup:
    st.info("⚠️ L'effort tranchant réduit V_lim est nul → vérification réduite ignorée.")

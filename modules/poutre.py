import streamlit as st
from datetime import datetime
import json
import math
import base64

def show():
    if st.session_state.get("retour_accueil_demande"):
        st.session_state.page = "Accueil"
        st.session_state.retour_accueil_demande = False
        st.experimental_rerun()

    st.markdown("## Poutre en béton armé")

    # --- BARRE DES 5 BOUTONS PRINCIPAUX ---
    btn_accueil, btn_reset, btn_save, btn_load, btn_pdf = st.columns(5)
    
    with btn_accueil:
        if st.button("🏠 Accueil", use_container_width=True):
            st.session_state.retour_accueil_demande = True
            st.experimental_rerun()
    
    with btn_reset:
        if st.button("🔄 Réinitialiser", use_container_width=True):
            st.rerun()
    
    with btn_save:
        dict_a_sauver = {k: v for k, v in st.session_state.items() if not k.startswith("_")}
        contenu_json = json.dumps(dict_a_sauver, indent=2)
        b64 = base64.b64encode(contenu_json.encode()).decode()
        href = f'<a href="data:file/json;base64,{b64}" download="poutre_donnees.json"><button style="width:100%">💾 Enregistrer</button></a>'
        st.markdown(href, unsafe_allow_html=True)
    
    with btn_load:
        uploaded_file = st.file_uploader("📂 Ouvrir", type="json", label_visibility="collapsed")
        if uploaded_file:
            donnees = json.load(uploaded_file)
            for k, v in donnees.items():
                st.session_state[k] = v
            st.success("✅ Données chargées")
            st.rerun()
    
    with btn_pdf:
        if st.button("📄 Générer PDF", use_container_width=True):
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
                V_lim=st.session_state.get("V_lim", 0)
            )
            with open(fichier_pdf, "rb") as f:
                st.download_button(
                    label="⬇️ Télécharger le rapport PDF",
                    data=f,
                    file_name=fichier_pdf,
                    mime="application/pdf"
                )
            st.success("✅ Rapport généré")


    # Données béton

    with open("beton_classes.json", "r") as f:
        beton_data = json.load(f)

    # Suite de ton code…
    input_col_gauche, result_col_droite = st.columns([2, 3])


    # --- COLONNE GAUCHE ---
    with input_col_gauche:
        st.markdown("### Informations sur le projet")
        st.text_input("", placeholder="Nom du projet", key="nom_projet")
        st.text_input("", placeholder="Partie", key="partie")

        date_col, indice_col = st.columns(2)
        with date_col:
            st.text_input("", placeholder="Date (jj/mm/aaaa)", value=datetime.today().strftime("%d/%m/%Y"), key="date")
        with indice_col:
            st.text_input("", placeholder="Indice", value="0", key="indice")

        st.markdown("### Caractéristiques de la poutre")
        beton_col, acier_col = st.columns(2)
        with beton_col:
            beton = st.selectbox("Classe de béton", list(beton_data.keys()), index=2)
        with acier_col:
            fyk = st.selectbox("Qualité d'acier [N/mm²]", ["400", "500"], index=1)

        section_col1, section_col2, section_col3 = st.columns(3)
        with section_col1:
            b = st.number_input("Larg. [cm]", 5, 1000, 20, key="b")
        with section_col2:
            h = st.number_input("Haut. [cm]", 5, 1000, 35, key="h")
        with section_col3:
            enrobage = st.number_input("Enrob. (cm)", min_value=0.0, max_value=100.0, value=5.0, step=0.1, key="enrobage")

        fck = beton_data[beton]["fck"]
        fck_cube = beton_data[beton]["fck_cube"]
        alpha_b = beton_data[beton]["alpha_b"]
        mu_val = beton_data[beton][f"mu_a{fyk}"]
        fyd = int(fyk) / 1.5

        st.markdown("### Sollicitations")
        moment_col, effort_col = st.columns(2)
        with moment_col:
            M_inf = st.number_input("Moment inférieur M (kNm)", 0.0, step=10.0)
            m_sup = st.checkbox("Ajouter un moment supérieur")
            M_max = M_inf
            if m_sup:
                M_sup = st.number_input("Moment supérieur M_sup (kNm)", 0.0, step=10.0)
                M_max = max(abs(M_inf), abs(M_sup))
        with effort_col:
            V = st.number_input("Effort tranchant V (kN)", 0.0, step=10.0)
            v_sup = st.checkbox("Ajouter un effort tranchant réduit")
            if v_sup:
                V_lim = st.number_input("Effort tranchant réduit V_limite (kN)", 0.0, step=10.0)

    # --- COLONNE DROITE ---
    with result_col_droite:
        st.markdown("### Dimensionnement")

        st.markdown("**⚙️ Vérification de la hauteur**")
        d_calcule = math.sqrt((M_max * 1e6) / (alpha_b * b * 10 * mu_val)) / 10
        st.markdown(f"**h,min** = {d_calcule:.1f} cm")
        hauteur_col, icone_col = st.columns([10, 1])
        with hauteur_col:
            st.markdown(f"h,min + enrobage = {d_calcule + enrobage:.1f} cm ≤ h = {h} cm")
        with icone_col:
            st.markdown("✅" if d_calcule + enrobage <= h else "❌")

        d = h - enrobage
        As_inf = (M_inf * 1e6) / (fyd * 0.9 * d * 10)
        As_min = 0.0013 * b * h * 1e2
        As_max = 0.04 * b * h * 1e2

        st.markdown("**⚙️ Armatures inférieures**" if not m_sup else "**Armatures inférieures**")

        as_col1, as_col2, as_col3 = st.columns(3)
        with as_col1:
            st.markdown(f"**Aₛ,inf = {As_inf:.0f} mm²**")
        with as_col2:
            st.markdown(f"**Aₛ,min = {As_min:.0f} mm²**")
        with as_col3:
            st.markdown(f"**Aₛ,max = {As_max:.0f} mm²**")

        choix_col1, choix_col2, choix_col3 = st.columns([3, 3, 4])
        with choix_col1:
            n_barres = st.selectbox("Nb barres", list(range(1, 11)), key="n_as_inf")
        with choix_col2:
            diam_barres = st.selectbox("Ø (mm)", [6, 8, 10, 12, 16, 20, 25, 32, 40], key="ø_as_inf")
        with choix_col3:
            As_choisi = n_barres * (math.pi * (diam_barres / 2) ** 2)
            ok1 = As_min <= As_choisi <= As_max and As_choisi >= As_inf
            st.markdown(f"Section choisie = **{As_choisi:.0f} mm²** {'✅' if ok1 else '❌'}")

        if m_sup:
            st.markdown("**⚙️ Armatures supérieures**")
            As_sup = (M_sup * 1e6) / (fyd * 0.9 * d * 10)
            sup_col1, sup_col2, sup_col3 = st.columns(3)
            with sup_col1:
                st.markdown(f"**Aₛ,sup = {As_sup:.0f} mm²**")
            with sup_col2:
                st.markdown(f"**Aₛ,min = {As_min:.0f} mm²**")
            with sup_col3:
                st.markdown(f"**Aₛ,max = {As_max:.0f} mm²**")

            choix_sup_col1, choix_sup_col2, choix_sup_col3 = st.columns([3, 3, 4])
            with choix_sup_col1:
                n_sup = st.selectbox("Nb barres", list(range(1, 11)), key="n_as_sup")
            with choix_sup_col2:
                d_sup = st.selectbox("Ø (mm)", [6, 8, 10, 12, 16, 20, 25, 32, 40], key="ø_as_sup")
            with choix_sup_col3:
                As_sup_choisi = n_sup * (math.pi * (d_sup / 2) ** 2)
                ok2 = As_min <= As_sup_choisi <= As_max and As_sup_choisi >= As_sup
                st.markdown(f"Section choisie = **{As_sup_choisi:.0f} mm²** {'✅' if ok2 else '❌'}")
                
                # === Vérification de l'effort tranchant standard ===

        if V > 0:
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
            col1, col2, col3 = st.columns(3)
            with col1:
                n_etriers = st.selectbox("Nbr. étriers", list(range(1, 5)), key="n_etriers")
            with col2:
                d_etrier = st.selectbox("Ø étriers (mm)", [6, 8, 10], key="ø_etrier")
            with col3:
                pas_choisi = st.number_input("Pas choisi (cm)", min_value=5.0, max_value=50.0, step=0.5, key="pas_etrier")
        
            Ast_etrier = n_etriers * math.pi * (d_etrier / 2) ** 2
            pas_theorique = Ast_etrier * fyd * d * 10 / (10 * V * 1e3)
            st.markdown(f"**Pas théorique = {pas_theorique:.1f} cm**")
        
            if pas_choisi <= pas_theorique:
                icone_pas = "✅"
            elif pas_choisi <= 30:
                icone_pas = "⚠️"
            else:
                icone_pas = "❌"
        
            st.markdown(f"**→ Pas choisi = {pas_choisi:.1f} cm {icone_pas}**")
        
        # === Vérification de l'effort tranchant réduit (si activé) ===
        
        if v_sup and V_lim > 0:
            st.markdown("**⚙️ Vérification de l'effort tranchant réduit**")
        
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
            pas_theorique_r = Ast_etrier_r * fyd * d * 10 / (10 * V_lim * 1e3)
            st.markdown(f"**Pas théorique (réduit) = {pas_theorique_r:.1f} cm**")
        
            if pas_choisi_r <= pas_theorique_r:
                icone_pas_r = "✅"
            elif pas_choisi_r <= 30:
                icone_pas_r = "⚠️"
            else:
                icone_pas_r = "❌"
        
            st.markdown(f"**→ Pas choisi = {pas_choisi_r:.1f} cm {icone_pas_r}**")

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ✅ Initialisation session
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "retour_accueil_demande" not in st.session_state:
    st.session_state.retour_accueil_demande = False

if st.session_state.retour_accueil_demande:
    st.session_state.page = "Accueil"
    st.session_state.retour_accueil_demande = False
    st.rerun()

def show():
    # Titre
    st.markdown("## Évolution de la résistance du béton selon l'EC2")

    # 🏠 Bouton Accueil
    if st.button("🏠 Accueil", use_container_width=True, key="btn_accueil_age"):
        st.session_state.retour_accueil_demande = True
        st.rerun()

    # Colonnes interface
    col_gauche, col_droite = st.columns([1, 1.2])

    with col_gauche:
        # Choix béton selon norme
        beton_label = st.selectbox("Choisir un type de béton :", [
            "C20/25", "C25/30", "C30/37", "C35/45", "C40/50", "C45/55", "C50/60"
        ])

        try:
            fck = int(beton_label.split("/")[0].replace("C", ""))
            fcm = fck + 8
        except Exception as e:
            st.error("Erreur dans la lecture du type de béton. Format attendu : C30/37")
            return

        # Ciment
        type_ciment = st.selectbox("Choisir le type de ciment :", ["prise rapide", "prise normale", "prise lente"])
        s_dict = {"prise rapide": 0.20, "prise normale": 0.25, "prise lente": 0.38}
        s = s_dict[type_ciment]

        # Âge béton
        t_selected = st.slider("Âge du béton (en jours)", 0, 28, 14)

        # Résistance mesurée (optionnel)
        res_mesuree = st.number_input("Résistance mesurée (en MPa, optionnel) :", min_value=0.0, value=0.0, step=0.1)

    # Courbe fck(t)
    t = np.linspace(1, 40, 500)
    beta_cc = np.exp(s * (1 - np.sqrt(28 / t)))
    fck_t = np.where(t < 28, beta_cc * fcm - 8, fck)

    # Résistance à t sélectionné
    if t_selected < 28:
        beta_val = np.exp(s * (1 - np.sqrt(28 / t_selected)))
        fck_val = beta_val * fcm - 8
    else:
        fck_val = fck

    # Estimation âge si mesure fournie
    estimated_age = None
    if 0 < res_mesuree < fck:
        beta_m = (res_mesuree + 8) / fcm
        log_val = np.log(beta_m)
        sqrt_val = 1 - log_val / s
        if sqrt_val > 0:
            estimated_age = 28 / (sqrt_val ** 2)

    # 📈 Graphe
    with col_droite:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(t, fck_t, label="fck(t)", linewidth=2)
        ax.axvline(x=t_selected, color='red', linestyle='--', label=f"Jour sélectionné : {t_selected} j")
        ax.axhline(y=fck_val, color='green', linestyle='--', label=f"Résistance à {t_selected} j : {fck_val:.2f} MPa")
        if res_mesuree > 0:
            ax.axhline(y=res_mesuree, color='orange', linestyle=':', label=f"Mesure : {res_mesuree} MPa")
            if estimated_age:
                ax.axvline(x=estimated_age, color='purple', linestyle=':', label=f"Âge estimé : {estimated_age:.1f} j")

        ax.set_xlabel("Âge du béton (jours)")
        ax.set_ylabel("Résistance à la compression fck(t) [MPa]")
        ax.set_title(f"Évolution de la résistance - Béton {beton_label} - {type_ciment}")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)

    # Résultats + formule
    with col_gauche:
        st.markdown("### Résultats :")
        st.markdown(f"🧱 Avec un béton **{beton_label}**, sa résistance est estimée à **{fck_val:.2f} MPa** après **{t_selected} jours**.")
        st.markdown("📊 Comparaison : C20/25 < C25/30 < C30/37 < C35/45 < C40/50 < C45/55 < C50/60")

        # Formules
        st.markdown("### Formule utilisée :")
        st.latex(r"f_{ck}(t) = \beta_{cc}(t) \cdot f_{cm} - 8")
        st.latex(fr"\beta_{{cc}}(t) = \exp\left({s} \cdot \left(1 - \sqrt{{28 / {t_selected}}}\right)\right)")
        beta_display = np.exp(s * (1 - np.sqrt(28 / t_selected)))
        st.latex(fr"f_{{ck}}({t_selected}) = {beta_display:.3f} \cdot {fcm} - 8 = {fck_val:.2f} \ \text{{MPa}}")

        if estimated_age:
            st.success(f"🟣 Âge estimé du béton pour {res_mesuree:.2f} MPa : **{estimated_age:.1f} jours**")
        elif res_mesuree > 0:
            st.warning("⚠️ La résistance mesurée dépasse fck → âge > 28 jours ou incohérence.")

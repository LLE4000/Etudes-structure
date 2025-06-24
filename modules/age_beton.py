import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

def show():
    # Titre de la page
    st.title("Évolution de la résistance du béton selon l'EC2")

    # Saisie du type de béton
    fck_label = st.selectbox("Choisir un type de béton (valeur de fck en MPa) :", [25, 30, 35, 40, 45, 50])
    fck = float(fck_label)
    fcm = fck + 8

    # Choix du type de ciment
    type_ciment = st.selectbox("Choisir le type de ciment :", ["prise rapide", "prise normale", "prise lente"])
    s_dict = {
        "prise rapide": 0.20,
        "prise normale": 0.25,
        "prise lente": 0.38
    }
    s = s_dict[type_ciment]

    # Jour sélectionné pour analyse
    t_selected = st.slider("Âge du béton (en jours)", 1, 50, 14)

    # (Optionnel) Entrée de résistance mesurée
    res_mesuree = st.number_input("Résistance mesurée (en MPa, optionnel) :", min_value=0.0, value=0.0, step=0.1)

    t = np.linspace(1, 50, 500)
    beta_cc = np.exp(s * (1 - np.sqrt(28 / t)))
    fck_t = np.where(t < 28, beta_cc * fcm - 8, fck)

    # Calcul du point sélectionné
    t_val = t_selected
    if t_val < 28:
        beta_val = np.exp(s * (1 - np.sqrt(28 / t_val)))
        fck_val = beta_val * fcm - 8
    else:
        fck_val = fck

    # Estimation de l'âge si une résistance est donnée
    estimated_age = None
    if res_mesuree > 0 and res_mesuree < fck:
        beta_m = (res_mesuree + 8) / fcm
        log_val = np.log(beta_m)
        sqrt_val = 1 - log_val / s
        if sqrt_val > 0:
            estimated_age = 28 / (sqrt_val ** 2)

    # Tracé du graphique
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(t, fck_t, label="fck(t)", linewidth=2)
    ax.axvline(x=t_val, color='red', linestyle='--', label=f"Jour sélectionné : {t_val} j")
    ax.axhline(y=fck_val, color='green', linestyle='--', label=f"Résistance à {t_val} j : {fck_val:.1f} MPa")
    if res_mesuree > 0:
        ax.axhline(y=res_mesuree, color='orange', linestyle=':', label=f"Mesure : {res_mesuree} MPa")
        if estimated_age:
            ax.axvline(x=estimated_age, color='purple', linestyle=':', label=f"Âge estimé : {estimated_age:.1f} j")

    ax.set_xlabel("Âge du béton (jours)")
    ax.set_ylabel("Résistance à la compression fck(t) [MPa]")
    ax.set_title(f"Évolution de la résistance - Béton C{int(fck)}/{int(fck+7)} - {type_ciment}")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

    # Résumé numérique
    st.markdown("### Résultats :")
    st.write(f"**fck =** {fck} MPa")
    st.write(f"**fcm =** {fcm} MPa")
    st.write(f"**s =** {s} (type de ciment : {type_ciment})")
    st.write(f"**Résistance à {t_val} jours :** {fck_val:.2f} MPa")
    if estimated_age:
        st.write(f"**Âge estimé du béton pour {res_mesuree} MPa :** {estimated_age:.2f} jours")
    elif res_mesuree > 0:
        st.write("**Attention : la résistance mesurée dépasse fck → âge > 28 j ou incohérence.**")

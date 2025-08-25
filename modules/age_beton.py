import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ==============================
# Utilitaires EC2
# ==============================
CLASSES = ["C20/25", "C25/30", "C30/37", "C35/45", "C40/50", "C45/55", "C50/60"]
CIMENT_S = {"prise rapide": 0.20, "prise normale": 0.25, "prise lente": 0.38}

def parse_fck(label: str) -> int:
    return int(label.split("/")[0].replace("C", ""))

def beta_cc(t_days, s: float):
    t = np.asarray(t_days, dtype=float)
    return np.exp(s * (1.0 - np.sqrt(28.0 / t)))

def fck_of_age(fck28: float, s: float, t_days):
    fcm = fck28 + 8.0
    t = np.asarray(t_days, dtype=float)
    val = beta_cc(t, s) * fcm - 8.0
    return np.where(t < 28.0, val, fck28)

def t_equivalent_for_target(fck28: float, s: float, target_MPa: float):
    # retourne t_eq (j) si atteignable < 28 j, sinon None
    if target_MPa <= 0 or target_MPa > fck28 + 1e-9:
        return None
    fcm = fck28 + 8.0
    ratio = (target_MPa + 8.0) / fcm
    if ratio <= 0:
        return None
    y = np.log(ratio)
    denom = (1.0 - y / s)
    if abs(denom) < 1e-12:
        return None
    t_eq = 28.0 / (denom ** 2)
    return float(t_eq) if 1.0 <= t_eq <= 28.0 else None

# ==============================
# Page
# ==============================
def show():
    st.markdown("## Évolution de la résistance du béton selon l'EC2")

    if st.button("🏠 Accueil", use_container_width=True, key="btn_accueil_age"):
        st.session_state.retour_accueil_demande = True
        st.rerun()

    col_g, col_d = st.columns([1, 1.4])

    # --------- Paramètres béton de référence (colonne gauche)
    with col_g:
        beton_label = st.selectbox("Choisir un type de béton (référence) :", CLASSES, index=0)
        fck28_ref = parse_fck(beton_label)

        type_ciment = st.selectbox("Choisir le type de ciment :", list(CIMENT_S.keys()), index=0)
        s = CIMENT_S[type_ciment]

        t_selected = st.slider("Âge du béton (en jours)", 1, 40, 14)
        res_mesuree = st.number_input("Résistance mesurée (MPa, optionnel) :", min_value=0.0, value=0.0, step=0.1)

    # Courbe & valeurs de référence
    t = np.linspace(1, 40, 500)
    fck_curve = fck_of_age(fck28_ref, s, t)
    fck_val = float(fck_of_age(fck28_ref, s, t_selected))

    # Éventuelle estimation d'âge depuis une mesure
    estimated_age = None
    if 0 < res_mesuree <= fck28_ref + 1e-9:
        fcm_ref = fck28_ref + 8.0
        ratio = (res_mesuree + 8.0) / fcm_ref
        if ratio > 0:
            y = np.log(ratio)
            denom = (1.0 - y / s)
            if abs(denom) > 1e-12:
                estimated_age = 28.0 / (denom ** 2)

    # --------- Graphe (colonne droite)
    with col_d:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(t, fck_curve, label=f"{beton_label} ({type_ciment})", linewidth=2)
        ax.axvline(x=t_selected, linestyle='--', label=f"{t_selected} j")
        ax.axhline(y=fck_val, linestyle='--', label=f"fck = {fck_val:.2f} MPa")
        if res_mesuree > 0:
            ax.axhline(y=res_mesuree, linestyle=':', label=f"Mesure {res_mesuree:.2f} MPa")
            if estimated_age:
                ax.axvline(x=estimated_age, linestyle=':', label=f"Âge estimé {estimated_age:.1f} j")

    # --------- COMPARATEUR (colonne gauche uniquement)
    with col_g:
        st.divider()
        st.markdown("### Comparateur d'équivalence")

        # cible = fck référence au jour sélectionné, sauf si une mesure est fournie
        target = float(res_mesuree) if res_mesuree > 0 else fck_val

        mode = st.radio("Mode", ["Une classe", "Plusieurs classes"], horizontal=True)

        if mode == "Une classe":
            alt_label = st.selectbox("Comparer avec :", CLASSES, index=2)
            type_ciment_alt = st.selectbox("Ciment (classe comparée) :", list(CIMENT_S.keys()),
                                           index=list(CIMENT_S.keys()).index(type_ciment))
            s_alt = CIMENT_S[type_ciment_alt]
            fck28_alt = parse_fck(alt_label)

            t_eq = t_equivalent_for_target(fck28_alt, s_alt, target)
            # Affichage court
            if t_eq is not None:
                st.success(f"{alt_label} ({type_ciment_alt}) atteint ≈ {target:.2f} MPa vers **{t_eq:.1f} j**.")
            else:
                st.warning(f"{alt_label} n’atteint pas {target:.2f} MPa avant 28 j (fck(28) = {fck28_alt} MPa).")

            # Ajoute la courbe comparée côté graphe
            with col_d:
                fck_curve_alt = fck_of_age(fck28_alt, s_alt, t)
                ax.plot(t, fck_curve_alt, label=f"{alt_label} ({type_ciment_alt})", linewidth=2)
                if t_eq is not None:
                    ax.axvline(x=t_eq, linestyle='--', alpha=0.8, label=f"t_eq {alt_label} ≈ {t_eq:.1f} j")

        else:
            # Tableau simplifié : Classe | fck(t sélectionné) | t_eq pour atteindre la cible
            rows = []
            for cls in CLASSES:
                fck28_alt = parse_fck(cls)
                fck_at_t = float(fck_of_age(fck28_alt, s, t_selected))  # même type de ciment que la réf par défaut
                t_eq = t_equivalent_for_target(fck28_alt, s, target)
                rows.append({
                    "Classe": cls,
                    f"fck({t_selected} j) [MPa]": f"{fck_at_t:.2f}",
                    "t_eq pour atteindre [j]": f"{t_eq:.1f}" if t_eq is not None else "≥ 28 (non atteint)",
                })
            st.dataframe(rows, use_container_width=True)

    # Finalise et affiche le graphe
    ax.set_xlabel("Âge du béton (jours)")
    ax.set_ylabel("Résistance fck(t) [MPa]")
    ax.set_title(f"Évolution de la résistance — {beton_label} — {type_ciment}")
    ax.grid(True)
    ax.legend()
    with col_d:
        st.pyplot(fig)

    # Bloc court “Référence”
    with col_g:
        st.markdown("### Référence")
        st.markdown(
            f"**{beton_label}** ({type_ciment}) → fck({t_selected} j) = **{fck_val:.2f} MPa**."
        )
        st.latex(r"f_{ck}(t)=\beta_{cc}(t)\,f_{cm}-8,\quad f_{cm}=f_{ck}+8,\quad \beta_{cc}(t)=\exp\!\big(s\,\big[1-\sqrt{28/t}\big]\big)")

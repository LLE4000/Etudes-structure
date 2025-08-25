import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ==============================
# Utilitaires EC2
# ==============================
CLASSES = ["C20/25", "C25/30", "C30/37", "C35/45", "C40/50", "C45/55", "C50/60"]
CIMENT_S = {"prise rapide": 0.20, "prise normale": 0.25, "prise lente": 0.38}

def parse_fck(label: str) -> int:
    # "C30/37" -> 30
    return int(label.split("/")[0].replace("C", ""))

def beta_cc(t_days: np.ndarray | float, s: float) -> np.ndarray | float:
    # EC2: β_cc(t) = exp{s(1 - sqrt(28/t))} (valable avant 28 j)
    t = np.asarray(t_days, dtype=float)
    return np.exp(s * (1.0 - np.sqrt(28.0 / t)))

def fck_of_age(fck28: float, s: float, t_days: np.ndarray | float) -> np.ndarray | float:
    """Retourne f_ck(t) (MPa) avec plafonnement à f_ck à 28 j comme dans ton module."""
    fcm = fck28 + 8.0
    t = np.asarray(t_days, dtype=float)
    val = beta_cc(t, s) * fcm - 8.0
    # au-delà de 28 j on borne à fck28 (même logique que ton code)
    val = np.where(t < 28.0, val, fck28)
    return val

def t_equivalent_for_target(fck28: float, s: float, target_MPa: float) -> float | None:
    """
    Âge t_eq (j) tel que f_ck(t_eq) == target, si atteignable avant 28 j.
    Forme analytique issue de :
      target = exp{s(1 - sqrt(28/t))} * fcm - 8
    => t = 28 / (1 - ln((target+8)/fcm)/s)^2
    Renvoie None si target <= 0, si ln(...) est invalide, ou si target > fck28.
    """
    if target_MPa <= 0:
        return None
    if target_MPa > fck28 + 1e-9:
        # Dans ton modèle, on plafonne à fck28 à partir de 28 j : cible non atteignable < 28 j
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
    if 1.0 <= t_eq <= 28.0:
        return float(t_eq)
    # Si > 28 : accessible seulement à 28 j avec fck28 (dans ton modèle)
    return None

# ==============================
# Page
# ==============================
def show():
    st.markdown("## Évolution de la résistance du béton selon l'EC2")

    if st.button("🏠 Accueil", use_container_width=True, key="btn_accueil_age"):
        st.session_state.retour_accueil_demande = True
        st.rerun()

    col_g, col_d = st.columns([1, 1.4])

    # --------- Paramètres béton de référence
    with col_g:
        beton_label = st.selectbox("Choisir un type de béton (référence) :", CLASSES, index=0)
        fck28_ref = parse_fck(beton_label)
        type_ciment = st.selectbox("Choisir le type de ciment :", list(CIMENT_S.keys()), index=0)
        s = CIMENT_S[type_ciment]

        t_selected = st.slider("Âge du béton (en jours)", 1, 40, 14)
        res_mesuree = st.number_input("Résistance mesurée (MPa, optionnel) :", min_value=0.0, value=0.0, step=0.1)

    # Courbe fck(t) pour le béton de référence
    t = np.linspace(1, 40, 500)
    fck_curve = fck_of_age(fck28_ref, s, t)
    fck_val = float(fck_of_age(fck28_ref, s, t_selected))

    # Si une mesure est fournie, on propose l'âge correspondant (dans le modèle)
    estimated_age = None
    if 0 < res_mesuree <= fck28_ref + 1e-9:
        fcm_ref = fck28_ref + 8.0
        ratio = (res_mesuree + 8.0) / fcm_ref
        if ratio > 0:
            y = np.log(ratio)
            denom = (1.0 - y / s)
            if abs(denom) > 1e-12:
                estimated_age = 28.0 / (denom ** 2)

    # --------- Comparateur d’équivalence
    st.divider()
    st.markdown("### Comparateur d’équivalence de résistance (décoffrage plus tôt ?)")

    target_source = "Référence (fck à t sélectionné)"
    target = fck_val
    if res_mesuree > 0:
        target_source = "Mesure fournie"
        target = float(res_mesuree)

    st.caption(f"🎯 **Cible** utilisée pour la comparaison : **{target:.2f} MPa** ({target_source}).")

    comp_mode = st.radio("Mode comparaison", ["Une classe", "Plusieurs classes"], horizontal=True)

    # ---- Graphe principal (référence)
    with col_d:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(t, fck_curve, label=f"{beton_label} ({type_ciment})", linewidth=2)
        ax.axvline(x=t_selected, color='red', linestyle='--', label=f"Jour sélectionné : {t_selected} j")
        ax.axhline(y=fck_val, color='green', linestyle='--', label=f"fck({t_selected} j) = {fck_val:.2f} MPa")
        if res_mesuree > 0:
            ax.axhline(y=res_mesuree, color='orange', linestyle=':', label=f"Mesure : {res_mesuree:.2f} MPa")
            if estimated_age:
                ax.axvline(x=estimated_age, color='purple', linestyle=':', label=f"Âge estimé : {estimated_age:.1f} j")

    # ------------------ Comparaison 1-à-1
    if comp_mode == "Une classe":
        col_c1, col_c2 = st.columns([1, 1.4])

        with col_c1:
            alt_label = st.selectbox("Comparer avec :", CLASSES, index=2, key="alt_cls")
            type_ciment_alt = st.selectbox("Ciment pour la classe comparée :", list(CIMENT_S.keys()), index=list(CIMENT_S.keys()).index(type_ciment), key="alt_cem")
            s_alt = CIMENT_S[type_ciment_alt]
            fck28_alt = parse_fck(alt_label)

            t_eq = t_equivalent_for_target(fck28_alt, s_alt, target)

            # Texte synthèse
            if t_eq is not None:
                st.success(
                    f"✅ **Équivalence** : un béton **{alt_label}** ({type_ciment_alt}) "
                    f"atteint **≈ {target:.2f} MPa** vers **{t_eq:.1f} jours**."
                )
                if t_eq < t_selected:
                    st.info(f"→ Gain potentiel : **{t_selected - t_eq:.1f} jours** plus tôt que {beton_label}.")
            else:
                st.warning(
                    f"⛔ La cible **{target:.2f} MPa** n’est pas atteignable par **{alt_label}** avant **28 j** "
                    f"dans ce modèle (fck(28) = {fck28_alt} MPa)."
                )

            # Quelques repères utiles
            f7 = fck_of_age(fck28_alt, s_alt, 7)
            f10 = fck_of_age(fck28_alt, s_alt, 10)
            f14 = fck_of_age(fck28_alt, s_alt, 14)
            st.markdown(
                f"**Repères {alt_label}** — fck(7 j) = {float(f7):.2f} MPa, "
                f"fck(10 j) = {float(f10):.2f} MPa, fck(14 j) = {float(f14):.2f} MPa."
            )

        with col_c2:
            # Trace la courbe de la classe comparée + marqueurs
            fck_curve_alt = fck_of_age(fck28_alt, s_alt, t)
            ax.plot(t, fck_curve_alt, label=f"{alt_label} ({type_ciment_alt})", linewidth=2)
            ax.axhline(y=target, color='gray', linestyle='--', alpha=0.6)
            if t_eq is not None:
                ax.axvline(x=t_eq, color='gray', linestyle='--', alpha=0.8, label=f"tₑq({alt_label}) ≈ {t_eq:.1f} j")

    # ------------------ Comparaison multi-classes (tableau)
    else:
        rows = []
        for cls in CLASSES:
            fck28_alt = parse_fck(cls)
            t_eq = t_equivalent_for_target(fck28_alt, s, target)  # même type de ciment par défaut
            rows.append({
                "Classe": cls,
                "fck(28j) [MPa]": fck28_alt,
                "t_eq pour atteindre cible [j]": f"{t_eq:.1f}" if t_eq is not None else "≥ 28 (non atteint)",
                "fck(7j) [MPa]": f"{float(fck_of_age(fck28_alt, s, 7)):.2f}",
                "fck(10j) [MPa]": f"{float(fck_of_age(fck28_alt, s, 10)):.2f}",
                "fck(14j) [MPa]": f"{float(fck_of_age(fck28_alt, s, 14)):.2f}",
            })
        st.dataframe(rows, use_container_width=True)

    # Finalise le graphe et affiche
    ax.set_xlabel("Âge du béton (jours)")
    ax.set_ylabel("Résistance à la compression fck(t) [MPa]")
    ax.set_title(f"Évolution de la résistance — Réf {beton_label} — {type_ciment}")
    ax.grid(True)
    ax.legend()
    with col_d:
        st.pyplot(fig)

    # --------- Résultats + formules
    with col_g:
        st.markdown("### Résultats (référence) :")
        st.markdown(
            f"🧱 Avec un béton **{beton_label}** ({type_ciment}), la résistance est estimée à "
            f"**{fck_val:.2f} MPa** après **{t_selected} jours**."
        )
        st.markdown("### Formule utilisée :")
        st.latex(r"f_{ck}(t) = \beta_{cc}(t)\, f_{cm} - 8,\quad f_{cm}=f_{ck}+8")
        st.latex(r"\beta_{cc}(t) = \exp\!\Big(s\,[1-\sqrt{28/t}]\Big)")
        beta_display = float(beta_cc(t_selected, s))
        fcm_ref = fck28_ref + 8.0
        st.latex(fr"f_{{ck}}({t_selected}) = {beta_display:.3f}\,\times\,{fcm_ref:.0f}\,-\,8 \;=\; {fck_val:.2f}\ \text{{MPa}}")

        if estimated_age:
            st.success(f"Âge estimé du béton pour {res_mesuree:.2f} MPa : **{estimated_age:.1f} jours**")
        elif res_mesuree > 0 and res_mesuree > fck28_ref:
            st.warning("⚠️ La résistance mesurée dépasse fck(28j) du béton de référence ;"
                       " le modèle simplifié borne la courbe à 28 jours.")

import streamlit as st
import json
import math
import pandas as pd
import matplotlib.pyplot as plt


@st.cache_data
def load_profiles():
    with open("profiles_test.json") as f:
        return json.load(f)


def calcul_contraintes(profile, M, V, fyk):
    Wel = profile["Wel"] * 1e3  # cm3 -> mm3
    Avz = profile["Avz"] * 1e2  # cm2 -> mm2

    sigma_n = M * 1e6 / Wel
    tau = V * 1e3 / Avz
    sigma_eq = math.sqrt(sigma_n**2 + 3 * tau**2)

    sigma_lim = fyk / 1.5
    tau_lim = fyk / (1.5 * math.sqrt(3))

    ratio_sigma = sigma_n / sigma_lim
    ratio_tau = tau / tau_lim
    ratio_eq = sigma_eq / sigma_lim

    return {
        "sigma_n": sigma_n,
        "tau": tau,
        "sigma_eq": sigma_eq,
        "max_ratio": max(ratio_sigma, ratio_tau, ratio_eq),
        "ratio_sigma": ratio_sigma,
        "ratio_tau": ratio_tau,
        "ratio_eq": ratio_eq
    }


def dessiner_profile(profile):
    h, b, tf, tw, r = (
        profile["h"],
        profile["b"],
        profile["tf"],
        profile["tw"],
        profile.get("r", 0),
    )
    scale = 0.5
    h *= scale
    b *= scale
    tf *= scale
    tw *= scale
    r *= scale

    fig, ax = plt.subplots(figsize=(4, 6))
    ax.set_aspect("equal")

    ax.add_patch(plt.Rectangle((-b / 2, h / 2 - tf), b, tf, color="gray"))
    ax.add_patch(plt.Rectangle((-tw / 2, -h / 2 + tf), tw, h - 2 * tf, color="lightgray"))
    ax.add_patch(plt.Rectangle((-b / 2, -h / 2), b, tf, color="gray"))

    ax.annotate(f"tf = {profile['tf']:.1f} mm", xy=(0, h / 2 + 3), ha="center")

    ax.set_xlim(-b, b)
    ax.set_ylim(-h, h)
    ax.axis("off")
    st.pyplot(fig)


def show():
    st.title("Choix de profilé métallique optimisé")
    profiles = load_profiles()

    col1, col2, col3 = st.columns(3)
    with col1:
        M = st.number_input("M [kN·m]", min_value=0.0, step=1.0)
    with col2:
        V = st.number_input("V [kN]", min_value=0.0, step=1.0)
    with col3:
        acier = st.selectbox("Acier", options=["S235", "S275", "S355"])

    fyk_label = {"S235": 235, "S275": 275, "S355": 355}
    fyk = fyk_label[acier]

    Iv_min = st.number_input("Iv min. [cm⁴] [optionnel]", min_value=0.0, step=1.0)

    st.markdown("### Filtrage par famille")
    familles = sorted(set(p["type"] for p in profiles.values()))
    familles_choisies = st.multiselect(
        "Types de profilés à inclure :", familles, default=["HEA"]
    )

    if M > 0 and V > 0:
        resultats = []
        for nom, prof in profiles.items():
            if prof["Iv"] is None or prof["Iv"] < Iv_min:
                continue
            if prof["type"] not in familles_choisies:
                continue

            contraintes = calcul_contraintes(prof, M, V, fyk)
            resultats.append({
                "Profilé": nom,
                "Type": prof["type"],
                "h": int(prof["h"]),
                "Wel": int(prof["Wel"]),
                "Avz": int(prof["Avz"]),
                "Iv": int(prof["Iv"]) if prof["Iv"] is not None else None,
                "Poids [kg/m]": int(prof["G"]),
                "σ [MPa]": round(contraintes["sigma_n"], 1),
                "τ [MPa]": round(contraintes["tau"], 1),
                "σeq [MPa]": round(contraintes["sigma_eq"], 1),
                "Utilisation": f"{round(contraintes['max_ratio']*100, 1)}%"
            })

        if not resultats:
            st.warning("Aucun profilé ne correspond aux critères.")
            return

        df = pd.DataFrame(resultats)
        df_sorted = df.copy()
        df_sorted["Uval"] = df_sorted["Utilisation"].str.replace("%", "").astype(float)
        df_sorted = df_sorted.sort_values("Uval").drop(columns=["Uval"])

        meilleur = (
            df_sorted[df_sorted["Utilisation"].str.replace("%", "").astype(float) <= 100]
            .iloc[-1]
            if any(df_sorted["Utilisation"].str.replace("%", "").astype(float) <= 100)
            else df_sorted.iloc[0]
        )

        col_g, col_d = st.columns([1.4, 1])

        with col_g:
            st.subheader("📌 Profilé optimal :")
            profil_choisi = st.selectbox(
                "Sélectionner un profilé :", df_sorted["Profilé"].tolist(),
                index=df_sorted["Profilé"].tolist().index(meilleur["Profilé"])
            )

            if st.checkbox("Afficher tous les profilés ✔/❌", value=True):
                def style_ligne(row):
                    val = float(row["Utilisation"].replace("%", ""))
                    color = "#d2f4d2" if val <= 100 else "#f7c2c2"
                    return [f"background-color: {color}"] * len(row)

                st.dataframe(df_sorted.style.apply(style_ligne, axis=1))

        with col_d:
            st.markdown(f"### {profil_choisi} ({profiles[profil_choisi]['type']})")
            st.write(
                pd.DataFrame(profiles[profil_choisi], index=["Valeur"]).T
                .loc[["type", "h", "b", "tw", "tf"]]
            )

            contraintes = calcul_contraintes(profiles[profil_choisi], M, V, fyk)
            st.markdown("### Section du profilé")
            dessiner_profile(profiles[profil_choisi])

            st.markdown("### Formules de dimensionnement")
            st.latex(
                r"\sigma_n = \frac{M \times 10^6}{W_{el}} = \frac{%.0f \times 10^6}{%.0f} = %.1f\ \text{MPa}"
                % (M, profiles[profil_choisi]["Wel"] * 1e3, contraintes["sigma_n"])
            )
            st.latex(
                r"\tau = \frac{V \times 10^3}{A_{vz}} = \frac{%.0f \times 10^3}{%.0f} = %.1f\ \text{MPa}"
                % (V, profiles[profil_choisi]["Avz"] * 1e2, contraintes["tau"])
            )
            st.latex(
                r"\sigma_{eq} = \sqrt{\sigma_n^2 + 3\tau^2} = %.1f\ \text{MPa}"
                % contraintes["sigma_eq"]
            )
            st.latex(
                r"\text{Utilisation} = \frac{\sigma_{eq}}{f_{yk}/1.5} = \frac{%.1f}{%.1f} = %.1f\%%"
                % (
                    contraintes["sigma_eq"],
                    fyk / 1.5,
                    contraintes["max_ratio"] * 100,
                )
            )
    else:
        st.info("Veuillez entrer M et V pour afficher les résultats.")

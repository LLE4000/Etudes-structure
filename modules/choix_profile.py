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
    Wel = profile["Wel"] * 1e3  # cm3 → mm3
    Avz = profile["Avz"] * 1e2  # cm2 → mm2

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
        "contrainte_limite": sigma_lim,
        "ratio_sigma": ratio_sigma,
        "ratio_tau": ratio_tau,
        "ratio_eq": ratio_eq
    }


def dessiner_profile(profile):
    h = profile["h"]
    b = profile["b"]
    tf = profile["tf"]
    tw = profile["tw"]
    r = profile.get("r", 0)

    scale = 0.5
    h *= scale
    b *= scale
    tf *= scale
    tw *= scale
    r *= scale

    fig, ax = plt.subplots(figsize=(3, 6))
    ax.set_aspect('equal')

    ax.add_patch(plt.Rectangle((-b/2, h/2 - tf), b, tf, color="gray"))
    ax.add_patch(plt.Rectangle((-tw/2, -h/2 + tf), tw, h - 2*tf, color="lightgray"))
    ax.add_patch(plt.Rectangle((-b/2, -h/2), b, tf, color="gray"))

    ax.annotate(f"tf = {profile['tf']:.1f} mm", xy=(0, h/2 + 2), ha="center")
    ax.axis("off")
    st.pyplot(fig)


def show():
    st.title("Choix de profilé métallique optimisé")

    profiles = load_profiles()
    fyk_label = {"S235": 235, "S275": 275, "S355": 355}

    colL, colR = st.columns([1.5, 1])

    with colL:
        col1, col2, col3 = st.columns(3)
        with col1:
            M = st.number_input("M [kN·m]", min_value=0.0, step=0.1)
        with col2:
            V = st.number_input("V [kN]", min_value=0.0, step=0.1)
        with col3:
            fyk = st.selectbox("Acier", options=list(fyk_label.keys()))

        inertie_min = st.number_input("Iv min. [cm⁴] [optionnel]", min_value=0.0, value=0.0)

        st.markdown("### Filtrage par famille")
        familles = sorted(set(p["type"] for p in profiles.values()))
        familles_choisies = st.multiselect("Types de profilés à inclure :", familles, default=["HEA"])

        if M > 0 and V > 0:
            resultats = []
            for name, prof in profiles.items():
                if prof["type"] not in familles_choisies or prof["Iv"] is None or prof["Iv"] < inertie_min:
                    continue
                contraintes = calcul_contraintes(prof, M, V, fyk_label[fyk])
                resultats.append({
                    "Profilé": name,
                    "Type": prof["type"],
                    "h": int(prof["h"]),
                    "Wel": int(prof["Wel"]),
                    "Avz": int(prof["Avz"]),
                    "Iv": int(prof["Iv"]) if prof["Iv"] is not None else None,
                    "Poids [kg/m]": f"{prof['G']:.0f}",
                    "σ [MPa]": f"{contraintes['sigma_n']:.1f}".rstrip("0").rstrip("."),
                    "τ [MPa]": f"{contraintes['tau']:.1f}".rstrip("0").rstrip("."),
                    "σeq [MPa]": f"{contraintes['sigma_eq']:.1f}".rstrip("0").rstrip("."),
                    "Utilisation": f"{contraintes['max_ratio'] * 100:.1f}%"
                })

            df = pd.DataFrame(resultats)
            df["Util_float"] = df["Utilisation"].str.rstrip("%").astype(float)
            df_sorted = df.sort_values("Util_float")
            meilleur = df_sorted[df_sorted["Util_float"] <= 100].iloc[-1] if any(df_sorted["Util_float"] <= 100) else df_sorted.iloc[0]

            st.subheader("📌 Profilé optimal :")
            profil_choisi = st.selectbox("Sélectionner un profilé :", df_sorted["Profilé"].tolist(), index=df_sorted["Profilé"].tolist().index(meilleur["Profilé"]))

            if st.checkbox("Afficher tous les profilés ✔/❌"):
                def surligner(row):
                    val = float(row["Utilisation"].rstrip("%"))
                    couleur = "#d4f7d4" if val <= 100 else "#f7c6c6"
                    return [f"background-color: {couleur}"] * len(row)

                st.dataframe(df_sorted.drop(columns="Util_float").style.apply(surligner, axis=1))

    with colR:
        if M > 0 and V > 0 and "profil_choisi" in locals():
            prof = profiles[profil_choisi]
            contraintes = calcul_contraintes(prof, M, V, fyk_label[fyk])

            st.markdown(f"### {profil_choisi} ({prof['type']})")
            st.table(pd.DataFrame({"Valeur": prof}).T)

            st.markdown("### Section du profilé")
            dessiner_profile(prof)

            st.subheader("Formules de dimensionnement")
            st.latex(r"\sigma_n = \frac{M \cdot 10^6}{W_{el}} = \frac{%s \cdot 10^6}{%s} = %.1f\ \text{MPa}" % (M, prof["Wel"] * 1e3, contraintes['sigma_n']))
            st.latex(r"\tau = \frac{V \cdot 10^3}{A_{vz}} = \frac{%s \cdot 10^3}{%s} = %.1f\ \text{MPa}" % (V, prof["Avz"] * 1e2, contraintes['tau']))
            st.latex(r"\sigma_{eq} = \sqrt{\sigma_n^2 + 3\tau^2} = %.1f\ \text{MPa}" % contraintes['sigma_eq'])
            st.latex(r"\text{Utilisation} = \frac{σ_{eq}}{f_{yk}/1.5} = \frac{%.1f}{%.1f} = %.1f\%%" % (
                contraintes['sigma_eq'], fyk_label[fyk]/1.5, contraintes['max_ratio'] * 100))
        else:
            st.info("Saisissez des valeurs de M et V pour afficher les résultats.")

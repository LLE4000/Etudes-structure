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

    sigma_lim = float(fyk) / 1.5
    tau_lim = float(fyk) / (1.5 * math.sqrt(3))
    sigma_eq_lim = sigma_lim

    ratio_sigma = sigma_n / sigma_lim
    ratio_tau = tau / tau_lim
    ratio_eq = sigma_eq / sigma_eq_lim

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

    fig, ax = plt.subplots(figsize=(4, 6))
    ax.set_aspect('equal')

    ax.add_patch(plt.Rectangle((-b/2, h/2 - tf), b, tf, color="gray"))
    ax.add_patch(plt.Rectangle((-tw/2, -h/2 + tf), tw, h - 2*tf, color="lightgray"))
    ax.add_patch(plt.Rectangle((-b/2, -h/2), b, tf, color="gray"))

    ax.annotate(f"h = {profile['h']:.0f} mm", xy=(b/2 + 5, 0), va="center")
    ax.annotate(f"b = {profile['b']:.0f} mm", xy=(0, -h/2 - 5), ha="center")
    ax.annotate(f"tf = {profile['tf']:.1f} mm", xy=(-b/2 + tf/2, h/2 + 2), ha="center")
    ax.annotate(f"tw = {profile['tw']:.1f} mm", xy=(0, 0), ha="center", va="center", color="black")
    ax.annotate(f"r = {r:.1f} mm", xy=(b/2 - r, -h/2 + tf + r), color="blue", ha="right")

    ax.set_xlim(-b, b)
    ax.set_ylim(-h, h)
    ax.axis("off")
    st.pyplot(fig)


def safe_int(val):
    try:
        return int(float(val))
    except:
        return None


def show():
    st.title("Choix de profilé métallique optimisé")
    profiles = load_profiles()

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        M = st.number_input("M [kN·m]", min_value=0.0, step=0.1)
    with col2:
        V = st.number_input("V [kN]", min_value=0.0, step=0.1)
    with col3:
        fyk_label = {"S235": 235, "S275": 275, "S355": 355}
        fyk = st.selectbox("Acier", options=list(fyk_label.keys()))

    inertie_min = st.number_input("Iv min. [cm⁴] [optionnel]", min_value=0.0, value=0.0)

    st.markdown("### Filtrage par famille")
    familles = sorted(set(p["type"] for p in profiles.values()))
    familles_choisies = st.multiselect(
        "Types de profilés à inclure :",
        familles,
        default=["HEA"]
    )

    if M > 0 and V > 0:
        resultats = []
        for name, prof in profiles.items():
            if prof.get("type") not in familles_choisies:
                continue
            if prof.get("Iv") in [None, "None", ""] or float(prof["Iv"]) < inertie_min:
                continue
            contraintes = calcul_contraintes(prof, M, V, fyk_label[fyk])
            resultats.append({
                "Profilé": name,
                "Type": prof.get("type", ""),
                "h": safe_int(prof.get("h")),
                "Wel": safe_int(prof.get("Wel")),
                "Avz": safe_int(prof.get("Avz")),
                "Iv": safe_int(prof.get("Iv")),
                "Poids [kg/m]": safe_int(prof.get("G")),
                "σ [MPa]": round(contraintes["sigma_n"], 1),
                "τ [MPa]": round(contraintes["tau"], 1),
                "σeq [MPa]": round(contraintes["sigma_eq"], 1),
                "Utilisation": f"{round(contraintes['max_ratio'] * 100, 1)}%"
            })

        df = pd.DataFrame(resultats)
        df_sorted = df.copy()
        df_sorted["Utilisation (%)"] = df_sorted["Utilisation"].str.replace('%', '').astype(float)
        df_sorted = df_sorted.sort_values("Utilisation (%)")

        meilleur = df_sorted[df_sorted["Utilisation (%)"] <= 100].iloc[-1] if any(df_sorted["Utilisation (%)"] <= 100) else df_sorted.iloc[0]

        st.subheader("📌 Profilé optimal :")
        profil_choisi = st.selectbox(
            "Sélectionner un profilé :",
            df_sorted["Profilé"].tolist(),
            index=df_sorted["Profilé"].tolist().index(meilleur["Profilé"])
        )

        if st.checkbox("Afficher tous les profilés ✔/❌", value=True):
            def surligner(row):
                valeur = float(row["Utilisation"].replace("%", ""))
                couleur = "background-color: #d4f7d4" if valeur <= 100 else "background-color: #f7c6c6"
                return [couleur] * len(row)

            st.dataframe(df_sorted.drop(columns=["Utilisation (%)"]).style.apply(surligner, axis=1))

        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.markdown(f"### {profil_choisi} ({profiles[profil_choisi]['type']})")
            st.write(pd.DataFrame({"Valeur": profiles[profil_choisi]}).T)

            contraintes = calcul_contraintes(profiles[profil_choisi], M, V, fyk_label[fyk])
            st.subheader("Formules de dimensionnement")
            st.latex(r"\sigma_n = \frac{M \times 10^6}{W_{el}} = \frac{%s \times 10^6}{%s} = %.1f\ \text{MPa}" % (
                M, profiles[profil_choisi]['Wel'] * 1e3, contraintes['sigma_n']))
            st.latex(r"\tau = \frac{V \times 10^3}{A_{vz}} = \frac{%s \times 10^3}{%s} = %.1f\ \text{MPa}" % (
                V, profiles[profil_choisi]['Avz'] * 1e2, contraintes['tau']))
            st.latex(r"\sigma_{eq} = \sqrt{\sigma_n^2 + 3\tau^2} = %.1f\ \text{MPa}" % contraintes['sigma_eq'])
            st.latex(r"\text{Utilisation} = \frac{\sigma_{eq}}{f_{yk}/1.5} = \frac{%.1f}{%.1f} = %.1f\%%" % (
                contraintes['sigma_eq'], fyk_label[fyk] / 1.5, contraintes['max_ratio'] * 100))
        with col2:
            st.markdown("### Section du profilé")
            dessiner_profile(profiles[profil_choisi])
    else:
        st.info("Veuillez entrer M et V pour afficher les résultats.")

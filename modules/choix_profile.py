import streamlit as st
import json
import math
import pandas as pd
import matplotlib.pyplot as plt


@st.cache_data
def load_profiles():
    with open("profiles_test.json") as f:
        return json.load(f)


def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def calcul_contraintes(profile, M, V, fyk):
    Wel = safe_float(profile.get("Wel"))  # cm³
    Avz = safe_float(profile.get("Avz"))  # cm²
    if Wel is None or Avz is None:
        return None

    Wel *= 1e3  # mm³
    Avz *= 1e2  # mm²

    sigma_n = M * 1e6 / Wel
    tau = V * 1e3 / Avz
    sigma_eq = math.sqrt(sigma_n**2 + 3 * tau**2)

    sigma_lim = fyk / 1.5
    tau_lim = fyk / (1.5 * math.sqrt(3))
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
        "ratio_eq": ratio_eq,
    }


def dessiner_profile(profile):
    h = safe_float(profile.get("h", 0))
    b = safe_float(profile.get("b", 0))
    tf = safe_float(profile.get("tf", 0))
    tw = safe_float(profile.get("tw", 0))
    r = safe_float(profile.get("r", 0)) or 0

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

    ax.annotate(f"tf = {profile['tf']} mm", xy=(0, h / 2 + 5), ha="center")

    ax.set_xlim(-b, b)
    ax.set_ylim(-h, h)
    ax.axis("off")
    st.pyplot(fig)


def format_decimal(x):
    if isinstance(x, float):
        return f"{x:.3f}".rstrip("0").rstrip(".")
    return x


def show():
    st.title("Choix de profilé métallique optimisé")
    profiles = load_profiles()

    col1, col2, col3 = st.columns(3)
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
    familles_choisies = st.multiselect("Types de profilés à inclure :", familles, default=["HEA"])

    if M > 0 and V > 0:
        resultats = []
        for name, prof in profiles.items():
            iv = safe_float(prof.get("Iv"))
            if iv is None or iv < inertie_min or prof["type"] not in familles_choisies:
                continue
            contraintes = calcul_contraintes(prof, M, V, fyk_label[fyk])
            if contraintes is None:
                continue
            resultats.append({
                "Profilé": name,
                "Type": prof["type"],
                "h": prof.get("h"),
                "Wel": prof.get("Wel"),
                "Avz": prof.get("Avz"),
                "Iv": prof.get("Iv"),
                "Poids [kg/m]": prof.get("G"),
                "σ [MPa]": contraintes["sigma_n"],
                "τ [MPa]": contraintes["tau"],
                "σeq [MPa]": contraintes["sigma_eq"],
                "Utilisation": contraintes["max_ratio"] * 100,
            })

        df = pd.DataFrame(resultats)
        df_sorted = df.sort_values("Utilisation")
        df_sorted = df_sorted.applymap(format_decimal)

        meilleur = df[df["Utilisation"].astype(float) <= 100]
        if not meilleur.empty:
            profil_defaut = meilleur.iloc[-1]["Profilé"]
        else:
            profil_defaut = df_sorted.iloc[0]["Profilé"]

        colG, colD = st.columns([1.3, 1])

        with colG:
            st.subheader("📌 Profilé optimal :")
            profil_choisi = st.selectbox(
                "Sélectionner un profilé :", df_sorted["Profilé"].tolist(),
                index=df_sorted["Profilé"].tolist().index(profil_defaut)
            )

            if st.checkbox("Afficher tous les profilés ✔/❌", value=True):
                def surligner(row):
                    try:
                        valeur = float(row["Utilisation"])
                        couleur = "#d4f7d4" if valeur <= 100 else "#f7c6c6"
                    except:
                        couleur = "white"
                    return [f"background-color: {couleur}"] * len(row)

                st.dataframe(df_sorted.style.apply(surligner, axis=1))

        with colD:
            st.markdown(f"### {profil_choisi} ({profiles[profil_choisi]['type']})")
            st.write(pd.DataFrame(profiles[profil_choisi], index=["Valeur"]).T)

            contraintes = calcul_contraintes(profiles[profil_choisi], M, V, fyk_label[fyk])
            if contraintes:
                st.markdown("### Section du profilé")
                dessiner_profile(profiles[profil_choisi])

                st.subheader("Formules de dimensionnement")
                st.latex(
                    r"\sigma_n = \frac{M \cdot 10^6}{W_{el}} = \frac{%s \cdot 10^6}{%s} = %.1f\ \text{MPa}"
                    % (M, profiles[profil_choisi]["Wel"] * 1e3, contraintes["sigma_n"])
                )
                st.latex(
                    r"\tau = \frac{V \cdot 10^3}{A_{vz}} = \frac{%s \cdot 10^3}{%s} = %.1f\ \text{MPa}"
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
                        fyk_label[fyk] / 1.5,
                        contraintes["max_ratio"] * 100,
                    )
                )
    else:
        st.info("Veuillez entrer M et V pour afficher les résultats.")

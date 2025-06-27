import streamlit as st
import json
import math
import pandas as pd
import matplotlib.pyplot as plt

# Charger les données JSON de profilés
@st.cache_data
def load_profiles():
    with open("profiles_test.json") as f:
        return json.load(f)

def calcul_contraintes(profile, M, V, fyk):
    Wel = profile["Wel"] * 1e3  # cm3 -> mm3
    Avz = profile["Avz"] * 1e2  # cm2 -> mm2

    sigma_n = M * 1e6 / Wel  # N/mm2
    tau = V * 1e3 / Avz       # N/mm2
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
        "ratio_eq": ratio_eq
    }

def show():
    st.title("Choix de profilé métallique optimisé")
    profiles = load_profiles()

    # 📉 Interface en deux colonnes
    col_gauche, col_droite = st.columns([1, 1.3])

    with col_gauche:
        st.header("Entrée des données")
        M = st.number_input("Moment fléchissant M [kN·m]", min_value=0.0, step=0.1)
        V = st.number_input("Effort tranchant V [kN]", min_value=0.0, step=0.1)
        fyk = st.selectbox("Acier", {"S235": 235, "S275": 275, "S355": 355})
        inertie_min = st.number_input("Inertie minimale Iv (cm4) [optionnel]", min_value=0.0, value=0.0)

        st.header("Filtrage par famille")
        familles = sorted(set(p["type"] for p in profiles.values()))
        familles_choisies = st.multiselect("Types de profilés à inclure :", familles, default=familles)

        if M > 0 and V > 0:
            resultats = []
            for name, prof in profiles.items():
                if prof["Iv"] < inertie_min or prof["type"] not in familles_choisies:
                    continue
                contraintes = calcul_contraintes(prof, M, V, fyk)
                resultats.append({
                    "Profilé": name,
                    "Type": prof["type"],
                    "h": prof["h"],
                    "Wel": prof["Wel"],
                    "Avz": prof["Avz"],
                    "Iv": prof["Iv"],
                    "Poids [kg/m]": prof["G"],
                    "\u03c3 [MPa]": round(contraintes["sigma_n"], 2),
                    "\u03c4 [MPa]": round(contraintes["tau"], 2),
                    "\u03c3eq [MPa]": round(contraintes["sigma_eq"], 2),
                    "Utilisation": round(contraintes["max_ratio"] * 100, 1)
                })

            df = pd.DataFrame(resultats)
            df_sorted = df.sort_values("Utilisation")
            meilleur = df_sorted[df_sorted["Utilisation"] <= 100].iloc[-1] if any(df_sorted["Utilisation"] <= 100) else df_sorted.iloc[0]

            st.subheader("\U0001f4cc Profilé optimal :")
            profil_choisi = st.selectbox("Sélectionner un profilé :", df_sorted["Profilé"].tolist(), index=df_sorted["Profilé"].tolist().index(meilleur["Profilé"]))

            if st.checkbox("Afficher tous les profilés ✔/❌"):
                def surligner(row):
                    couleur = "background-color: #d4f7d4" if row["Utilisation"] <= 100 else "background-color: #f7c6c6"
                    return [couleur] * len(row)
                st.dataframe(df_sorted.style.apply(surligner, axis=1))

    with col_droite:
        if M > 0 and V > 0:
            st.header("Visualisation du profilé")
            prof_data = profiles[profil_choisi]
            contraintes = calcul_contraintes(prof_data, M, V, fyk)

            st.markdown(f"### {profil_choisi} ({prof_data['type']})")
            st.write(pd.DataFrame({"Valeur": prof_data}).T)

            st.subheader("Formules de dimensionnement")
            st.latex(r"\sigma_n = \frac{M \times 10^6}{W_{el}} = \frac{%s \times 10^6}{%s} = %.2f\ \text{MPa}" % (M, prof_data['Wel'] * 1e3, contraintes['sigma_n']))
            st.latex(r"\tau = \frac{V \times 10^3}{A_{vz}} = \frac{%s \times 10^3}{%s} = %.2f\ \text{MPa}" % (V, prof_data['Avz'] * 1e2, contraintes['tau']))
            st.latex(r"\sigma_{eq} = \sqrt{\sigma_n^2 + 3\tau^2} = %.2f\ \text{MPa}" % contraintes['sigma_eq'])
            st.latex(r"\text{Utilisation} = \frac{\sigma_{eq}}{f_{yk}/1.5} = \frac{%.2f}{%.2f} = %.1f\%%" % (
                contraintes['sigma_eq'], fyk/1.5, contraintes['max_ratio'] * 100))
        else:
            st.info("Veuillez entrer M et V pour afficher les résultats.")

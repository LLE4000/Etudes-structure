import streamlit as st
import json
import math
import pandas as pd
import matplotlib.pyplot as plt

@st.cache_data
def load_profiles():
    with open("profiles_complet.json") as f:
        return json.load(f)

def calcul_contraintes(profile, M, V, fyk):
    Wel = profile["Wel"] * 1e3  # cm3 -> mm3
    Avz = profile["Avz"] * 1e2  # cm2 -> mm2

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
        "sigma_n": sigma_n, "tau": tau, "sigma_eq": sigma_eq,
        "max_ratio": max(ratio_sigma, ratio_tau, ratio_eq),
        "contrainte_limite": sigma_lim,
        "ratio_sigma": ratio_sigma,
        "ratio_tau": ratio_tau,
        "ratio_eq": ratio_eq
    }

def dessiner_profile(profile):
    h, b, tf, tw, r = profile["h"], profile["b"], profile["tf"], profile["tw"], profile["r"]
    fig, ax = plt.subplots(figsize=(3, 3))

    # Mise à l'échelle
    h /= 2
    b /= 2
    tf /= 2
    tw /= 2
    r /= 2

    # Ailes sup & inf
    ax.add_patch(plt.Rectangle((-b/2, h/2 - tf), b, tf, color='gray'))
    ax.add_patch(plt.Rectangle((-b/2, -h/2), b, tf, color='gray'))

    # Âme
    ax.add_patch(plt.Rectangle((-tw/2, -h/2 + tf), tw, h - 2*tf, color='lightgray'))

    # Côtes
    ax.annotate(f"h = {h*2:.0f} mm", xy=(0, 0), xytext=(b, 0), ha='left', va='center', arrowprops=dict(arrowstyle='<->'))
    ax.annotate(f"b = {b*2:.0f} mm", xy=(0, h/2+tf), xytext=(0, h/2+tf+5), ha='center')
    ax.annotate(f"tw = {tw*2:.1f}", xy=(0, -h/4), xytext=(b/1.5, -h/4), ha='left')
    ax.annotate(f"tf = {tf*2:.1f}", xy=(b/4, h/2 - tf/2), xytext=(b/1.5, h/2 - tf/2), ha='left')
    ax.annotate(f"r = {r*2:.1f}", xy=(-b/2 + r, -h/2 + tf + r), xytext=(-b, -h/2), fontsize=8)

    ax.set_xlim(-b, b)
    ax.set_ylim(-h, h)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

def show():
    st.title("Choix de profilé métallique optimisé")
    profiles = load_profiles()

    col_gauche, col_droite = st.columns([1, 1.3])

    with col_gauche:
        st.markdown("### Entrée des données")
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            M = st.number_input("Moment fléchissant M [kN·m]", min_value=0.0, step=0.1, key="moment")
        with c2:
            V = st.number_input("Effort tranchant V [kN]", min_value=0.0, step=0.1, key="effort")
        with c3:
            acier_dict = {"S235": 235, "S275": 275, "S355": 355}
            acier_nom = st.selectbox("Acier", list(acier_dict.keys()))
            fyk = acier_dict[acier_nom]

        inertie_min = st.number_input("Inertie minimale Iv (cm4) [optionnel]", min_value=0.0, value=0.0, format="%.1f", key="inertie")

        st.markdown("### Filtrage par famille")
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
                    "σ [MPa]": round(contraintes["sigma_n"], 2),
                    "τ [MPa]": round(contraintes["tau"], 2),
                    "σeq [MPa]": round(contraintes["sigma_eq"], 2),
                    "Utilisation": round(contraintes["max_ratio"] * 100, 1)
                })

            df = pd.DataFrame(resultats)
            df_sorted = df.sort_values("Utilisation")
            meilleur = df_sorted[df_sorted["Utilisation"] <= 100].iloc[-1] if any(df_sorted["Utilisation"] <= 100) else df_sorted.iloc[0]

            st.markdown("### 📌 Profilé optimal :")
            profil_choisi = st.selectbox("Sélectionner un profilé :", df_sorted["Profilé"].tolist(), index=df_sorted["Profilé"].tolist().index(meilleur["Profilé"]))

            if st.checkbox("Afficher tous les profilés ✔/❌"):
                def surligner(row):
                    couleur = "background-color: #d4f7d4" if row["Utilisation"] <= 100 else "background-color: #f7c6c6"
                    return [couleur] * len(row)
                st.dataframe(df_sorted.st_

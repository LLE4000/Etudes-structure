import streamlit as st
import json
import math
import pandas as pd
import matplotlib.pyplot as plt

@st.cache_data
def load_profiles():
    with open("profiles_test.json") as f:
        raw_profiles = json.load(f)
        clean_profiles = {}
        for name, prof in raw_profiles.items():
            try:
                clean_profiles[name] = {
                    "type": str(prof.get("type", "")),
                    "h": float(prof["h"]) if prof["h"] not in [None, ""] else None,
                    "b": float(prof["b"]) if prof["b"] not in [None, ""] else None,
                    "tw": float(prof["tw"]) if prof["tw"] not in [None, ""] else None,
                    "tf": float(prof["tf"]) if prof["tf"] not in [None, ""] else None,
                    "r": float(prof.get("r", 0)) if prof.get("r", 0) not in [None, ""] else 0,
                    "Wel": float(prof["Wel"]) if prof["Wel"] not in [None, ""] else None,
                    "Avz": float(prof["Avz"]) if prof["Avz"] not in [None, ""] else None,
                    "Iv": float(prof["Iv"]) if prof["Iv"] not in [None, ""] else None,
                    "G": float(prof["G"]) if prof["G"] not in [None, ""] else None,
                }
            except Exception:
                continue
        return clean_profiles

def calcul_contraintes(profile, M, V, fyk):
    Wel = profile["Wel"] * 1e3
    Avz = profile["Avz"] * 1e2
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
    h = profile["h"]
    b = profile["b"]
    tf = profile["tf"]
    tw = profile["tw"]
    r = profile.get("r", 0)
    scale = 0.4
    fig, ax = plt.subplots(figsize=(3, 4))
    ax.set_aspect('equal')
    ax.add_patch(plt.Rectangle((-b/2*scale, h/2*scale - tf*scale), b*scale, tf*scale, color="gray"))
    ax.add_patch(plt.Rectangle((-tw/2*scale, -h/2*scale + tf*scale), tw*scale, (h - 2*tf)*scale, color="lightgray"))
    ax.add_patch(plt.Rectangle((-b/2*scale, -h/2*scale), b*scale, tf*scale, color="gray"))
    ax.axis("off")
    st.pyplot(fig)

def format_float(val):
    return f"{val:.3f}".rstrip('0').rstrip('.') if isinstance(val, float) else val

def show():
    st.title("Choix de profilé métallique optimisé")
    profiles = load_profiles()

    col_left, col_right = st.columns([1.3, 1])

    with col_left:
        col1, col2, col3 = st.columns(3)
        with col1:
            M = st.number_input("M [kN·m]", min_value=0.0, step=10.0)
        with col2:
            V = st.number_input("V [kN]", min_value=0.0, step=10.0)
        with col3:
            fyk = st.selectbox("Acier", options=["S235", "S275", "S355"])
            fyk_val = {"S235": 235, "S275": 275, "S355": 355}[fyk]

        inertie_min = st.number_input("Iv min. [cm⁴] [optionnel]", min_value=0.0, value=0.0)

        familles = sorted(set(p["type"] for p in profiles.values()))
        familles_choisies = st.multiselect("Types de profilés à inclure :", familles, default=["HEA"])

        st.markdown("### 📌 Profilé optimal :")
        resultats = []
        for name, prof in profiles.items():
            if prof["Wel"] is None or prof["Avz"] is None or prof["type"] not in familles_choisies:
                continue
            if inertie_min and (prof["Iv"] is None or prof["Iv"] < inertie_min):
                continue
            contraintes = calcul_contraintes(prof, M, V, fyk_val)
            resultats.append({
                "Profilé": name,
                "Type": prof["type"],
                "h": format_float(prof["h"]),
                "Wel": format_float(prof["Wel"]),
                "Avz": format_float(prof["Avz"]),
                "Iv": format_float(prof["Iv"]),
                "Poids [kg/m]": format_float(prof["G"]),
                "σ [MPa]": format_float(contraintes["sigma_n"]),
                "τ [MPa]": format_float(contraintes["tau"]),
                "σeq [MPa]": format_float(contraintes["sigma_eq"]),
                "Utilisation": format_float(contraintes["max_ratio"] * 100)
            })

        if resultats:
            df = pd.DataFrame(resultats)
            df_sorted = df.sort_values("Utilisation")
            df_sorted["Utilisation"] = df_sorted["Utilisation"].astype(float)
            meilleur = df_sorted[df_sorted["Utilisation"] <= 100].iloc[-1] if any(df_sorted["Utilisation"] <= 100) else df_sorted.iloc[0]
            profil_choisi = st.selectbox("Sélectionner un profilé :", df_sorted["Profilé"].tolist(), index=df_sorted["Profilé"].tolist().index(meilleur["Profilé"]))

            if st.checkbox("Afficher tous les profilés ✔/❌", value=True):
                def surligner(row):
                    couleur = "background-color: #d4f7d4" if float(row["Utilisation"]) <= 100 else "background-color: #f7c6c6"
                    return [couleur] * len(row)
                st.dataframe(df_sorted.style.apply(surligner, axis=1), use_container_width=True)
        else:
            st.warning("Aucun profilé ne correspond aux critères.")

    with col_right:
        if resultats:
            st.markdown(f"### {profil_choisi} ({profiles[profil_choisi]['type']})")
            prof = profiles[profil_choisi]
            df_info = pd.DataFrame.from_dict({k: format_float(v) for k, v in prof.items()}, orient='index', columns=["Valeur"]).T
            st.table(df_info)

            st.markdown("### Section du profilé")
            dessiner_profile(prof)

            contraintes = calcul_contraintes(prof, M, V, fyk_val)
            st.markdown("### Formules de dimensionnement")
            st.latex(r"\sigma_n = \frac{M \times 10^6}{W_{el}} = \frac{%s \times 10^6}{%s} = %.2f\ \text{MPa}" % (M, prof['Wel'] * 1e3, contraintes['sigma_n']))
            st.latex(r"\tau = \frac{V \times 10^3}{A_{vz}} = \frac{%s \times 10^3}{%s} = %.2f\ \text{MPa}" % (V, prof['Avz'] * 1e2, contraintes['tau']))
            st.latex(r"\sigma_{eq} = \sqrt{\sigma_n^2 + 3\tau^2} = %.2f\ \text{MPa}" % contraintes['sigma_eq'])
            st.latex(r"\text{Utilisation} = \frac{\sigma_{eq}}{f_{yk}/1.5} = \frac{%.2f}{%.2f} = %.1f\%%" % (
                contraintes['sigma_eq'], fyk_val / 1.5, contraintes['max_ratio'] * 100))

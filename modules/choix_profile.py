import streamlit as st
import json
import math
import pandas as pd

@st.cache_data
def load_profiles():
    with open("profiles_test.json") as f:
        raw_profiles = json.load(f)
    clean_profiles = {}
    for name, prof in raw_profiles.items():
        try:
            clean_profiles[name] = {
                "h": int(prof["h"]),
                "Wel": float(prof["Wel"]),
                "Avz": float(prof["Avz"]),
                "Iv": None if prof["Iv"] in ("None", None) else float(prof["Iv"]),
                "Poids": float(prof["Poids"]),
                "type": prof["type"],
                "b": float(prof["b"]),
                "tw": float(prof["tw"]),
                "tf": float(prof["tf"]),
                "r": float(prof["r"]),
                "A": float(prof["A"])
            }
        except Exception as e:
            print(f"Erreur dans le profil {name} : {e}")
    print(f"\u2714\ufe0f {len(clean_profiles)} profils chargés depuis le JSON.")
    return clean_profiles

def calcul_contraintes(profile, M, V, fyk):
    Wel = profile["Wel"] * 1e3  # cm³ → mm³
    Avz = profile["Avz"] * 1e2  # cm² → mm²
    sigma_n = M * 1e6 / Wel     # en MPa
    tau = V * 1e3 / Avz         # en MPa
    sigma_eq = math.sqrt(sigma_n**2 + 3 * tau**2)
    utilisation = sigma_eq / (fyk / 1.5)
    return sigma_n, tau, sigma_eq, utilisation

def format_float(val, unit="", pourcentage=False):
    if isinstance(val, float):
        val = round(val, 1)
    if pourcentage:
        return f"{val:.1f}%"
    return f"{val:.1f} {unit}" if unit else f"{val:.1f}"

def show():
    st.title("Choix de profilé métallique optimisé")
    profiles = load_profiles()

    familles_disponibles = sorted(set(p["type"] for p in profiles.values()))

    col_left, col_right = st.columns([1.3, 1])

    with col_left:
        col1, col2, col3 = st.columns(3)
        with col1:
            M = st.number_input("M [kN·m]", min_value=0.0, step=10.0)
        with col2:
            V = st.number_input("V [kN]", min_value=0.0, step=10.0)
        with col3:
            acier = st.selectbox("Acier", ["S235", "S275", "S355"])
        fyk = int(acier[1:])

        Iv_min = st.number_input("Iv min. [cm⁴] [optionnel]", min_value=0.0, step=100.0)

        st.subheader("Filtrage par famille")
        familles_choisies = st.multiselect("Types de profilés à inclure :", options=familles_disponibles, default=["HEA"])

        profils_filtres = {
            k: v for k, v in profiles.items()
            if v["type"] in familles_choisies
        }

        donnees = []
        for nom, prof in profils_filtres.items():
            if prof["Iv"] is not None and Iv_min > 0 and prof["Iv"] < Iv_min:
                continue
            sigma_n, tau, sigma_eq, utilisation = calcul_contraintes(prof, M, V, fyk)
            donnees.append({
                "Utilisation": round(utilisation * 100, 1),
                "Profilé": nom,
                "h": prof["h"],
                "Wel": prof["Wel"],
                "Avz": prof["Avz"],
                "Iv": prof["Iv"],
                "Poids [kg/m]": prof["Poids"],
                "σ [MPa]": round(sigma_n, 1),
                "τ [MPa]": round(tau, 1),
                "σeq [MPa]": round(sigma_eq, 1),
            })

        donnees = sorted(donnees, key=lambda x: x["Utilisation"]) if donnees else []
        print(f"\u2714\ufe0f {len(donnees)} profils conservés après filtrage.")

        st.subheader("📌 Profilé optimal :")
        if donnees:
            meilleur_nom = donnees[0]["Profilé"]
            nom_selectionne = st.selectbox("Sélectionner un profilé :", options=[d["Profilé"] for d in donnees], index=0)
            afficher_tous = st.checkbox("Afficher tous les profilés ✓/✗", value=True)
            if afficher_tous:
                df = pd.DataFrame(donnees)
                df.drop(columns=["Type"], errors="ignore", inplace=True)
                st.dataframe(df.set_index("Profilé"))
        else:
            st.warning("Aucun profilé ne satisfait aux critères.")

    with col_right:
        if donnees:
            profil = profiles[nom_selectionne]
            st.markdown(f"### {nom_selectionne} ({profil['type']})")
            df_info = pd.DataFrame.from_dict({
                'Valeur': [profil[k] for k in ["type", "h", "b", "tw", "tf", "r", "A"]]
            }, orient='index', columns=['type', 'h', 'b', 'tw', 'tf', 'r', 'A']).T
            st.table(df_info)

            st.subheader("Formules de dimensionnement")
            sigma_n, tau, sigma_eq, utilisation = calcul_contraintes(profil, M, V, fyk)

            st.latex(
                r"\sigma_n = \frac{M \times 10^6}{W_{el} \times 10^3} = \frac{%.1f \times 10^6}{%.1f \times 10^3} = %.2f"
                % (M, profil["Wel"], sigma_n)
            )
            st.latex(
                r"\tau = \frac{V \times 10^3}{A_{vz} \times 10^2} = \frac{%.1f \times 10^3}{%.1f \times 10^2} = %.2f"
                % (V, profil["Avz"], tau)
            )
            st.latex(
                r"\sigma_{eq} = \sqrt{\sigma_n^2 + 3\tau^2} = \sqrt{%.2f^2 + 3 \times %.2f^2} = %.2f"
                % (sigma_n, tau, sigma_eq)
            )
            st.latex(
                r"\text{Utilisation} = \frac{\sigma_{eq}}{f_{yk}/1.5} = \frac{%.2f}{%.1f} = %.1f%%"
                % (sigma_eq, fyk / 1.5, utilisation * 100)
            )

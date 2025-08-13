import streamlit as st
import json
import math
import pandas as pd

# ---------- Chargement / nettoyage des profils ----------
@st.cache_data
def load_profiles():
    def pick(d, *keys, default=None):
        for k in keys:
            if k in d and d[k] not in (None, "None", ""):
                return d[k]
        return default

    with open("profiles_test.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    cleaned = {}
    for name, p in raw.items():
        try:
            # Champs attendus (avec correspondances vers ton JSON)
            h      = float(pick(p, "h"))
            Wel    = float(pick(p, "Wel"))                  # cm³
            Avz    = float(pick(p, "Avz"))                  # cm²
            Iv     = pick(p, "Iv", "Iy")                    # cm⁴ (optionnel)
            Iv     = None if Iv in (None, "None", "") else float(Iv)
            poids  = float(pick(p, "Poids", "masse"))       # kg/m
            typ    = str(pick(p, "type"))

            b      = float(pick(p, "b", default=0.0))
            tw     = float(pick(p, "tw", default=0.0))
            tf     = float(pick(p, "tf", default=0.0))
            r      = float(pick(p, "r",  default=0.0))
            A      = float(pick(p, "A",  default=0.0))

            # Vérifs mini pour éviter div/0 ensuite
            if Wel <= 0 or Avz <= 0:
                continue

            cleaned[name] = {
                "h": h, "Wel": Wel, "Avz": Avz, "Iv": Iv,
                "Poids": poids, "type": typ, "b": b, "tw": tw, "tf": tf, "r": r, "A": A
            }
        except Exception as e:
            # On ignore proprement les lignes corrompues
            print(f"⚠️ Profil ignoré ({name}) : {e}")

    return cleaned


# ---------- Calculs ----------
def calcul_contraintes(profile, M, V, fyk):
    # M [kN·m], V [kN], fyk [MPa]; Wel [cm³], Avz [cm²]
    Wel_mm3 = profile["Wel"] * 1e3   # cm³ → mm³
    Avz_mm2 = profile["Avz"] * 1e2   # cm² → mm²
    sigma_n = (M * 1e6) / Wel_mm3    # MPa
    tau     = (V * 1e3) / Avz_mm2    # MPa
    sigma_eq = math.sqrt(sigma_n**2 + 3 * tau**2)
    utilisation = sigma_eq / (fyk / 1.5)  # EC: fyd = fyk/γM; γM~1.5
    return sigma_n, tau, sigma_eq, utilisation


# ---------- UI ----------
def show():
    st.title("Choix de profilé métallique optimisé")

    profiles = load_profiles()
    if not profiles:
        st.error("Aucun profil n’a été chargé. Vérifie que **profiles_test.json** existe et contient des clés "
                 "`h`, `Wel`, `Avz`, `masse/Poids`, `type` (ton fichier actuel convient).")
        return

    familles_disponibles = sorted({p["type"] for p in profiles.values()})
    default_familles = ["HEA"] if "HEA" in familles_disponibles else familles_disponibles[:1]
    familles_choisies = st.multiselect(
        "Types de profilés à inclure :", options=familles_disponibles, default=default_familles
    )

    col_left, col_right = st.columns([1.3, 1])

    with col_left:
        col1, col2, col3 = st.columns(3)
        with col1:
            M = st.number_input("M [kN·m]", min_value=0.0, step=10.0, value=0.0)
        with col2:
            V = st.number_input("V [kN]", min_value=0.0, step=10.0, value=0.0)
        with col3:
            acier = st.selectbox("Acier", ["S235", "S275", "S355"], index=0)
        fyk = int(acier[1:])  # 235 / 275 / 355

        Iv_min = st.number_input("Iv min. [cm⁴] (optionnel)", min_value=0.0, step=100.0, value=0.0)

        # Filtrage par familles
        if familles_choisies:
            profils_filtres = {k: v for k, v in profiles.items() if v["type"] in familles_choisies}
        else:
            profils_filtres = profiles  # si rien coché → tout

        # Calculs
        donnees = []
        for nom, prof in profils_filtres.items():
            if prof["Iv"] is not None and Iv_min > 0 and prof["Iv"] < Iv_min:
                continue
            sigma_n, tau, sigma_eq, utilisation = calcul_contraintes(prof, M, V, fyk)
            donnees.append({
                "Utilisation [%]": round(utilisation * 100, 1),
                "Profilé": nom,
                "type": prof["type"],
                "h [mm]": int(prof["h"]),
                "Wel [cm³]": prof["Wel"],
                "Avz [cm²]": prof["Avz"],
                "Iv [cm⁴]": prof["Iv"],
                "Poids [kg/m]": prof["Poids"],
                "σ [MPa]": round(sigma_n, 1),
                "τ [MPa]": round(tau, 1),
                "σeq [MPa]": round(sigma_eq, 1),
            })

        donnees = sorted(donnees, key=lambda x: x["Utilisation [%]"]) if donnees else []

        st.subheader("📌 Profilé optimal :")
        if donnees:
            # sélecteur + tableau
            noms = [d["Profilé"] for d in donnees]
            nom_selectionne = st.selectbox("Sélectionner un profilé :", options=noms, index=0)
            afficher_tous = st.checkbox("Afficher tous les profilés ✓/✗", value=True)
            if afficher_tous:
                df = pd.DataFrame(donnees).set_index("Profilé")
                st.dataframe(df)
        else:
            st.warning("Aucun profilé ne satisfait aux critères.")

    with col_right:
        if donnees:
            profil = profiles[nom_selectionne]
            st.markdown(f"### {nom_selectionne} ({profil['type']})")

            props = {
                "h [mm]": profil["h"], "b [mm]": profil["b"], "tw [mm]": profil["tw"],
                "tf [mm]": profil["tf"], "r [mm]": profil["r"], "A [cm²]": profil["A"],
                "Wel [cm³]": profil["Wel"], "Avz [cm²]": profil["Avz"],
                "Iv [cm⁴]": profil["Iv"], "Poids [kg/m]": profil["Poids"]
            }
            st.table(pd.DataFrame(list(props.items()), columns=["Propriété", "Valeur"]))

            st.subheader("Formules de dimensionnement")
            sigma_n, tau, sigma_eq, utilisation = calcul_contraintes(profil, M, V, fyk)

            st.latex(
                r"\sigma_n = \frac{M \times 10^6}{W_{el} \times 10^3}"
                rf" = \frac{{{M:.1f} \times 10^6}}{{{profil['Wel']:.1f} \times 10^3}} = {sigma_n:.2f}\ \text{{MPa}}"
            )
            st.latex(
                r"\tau = \frac{V \times 10^3}{A_{vz} \times 10^2}"
                rf" = \frac{{{V:.1f} \times 10^3}}{{{profil['Avz']:.2f} \times 10^2}} = {tau:.2f}\ \text{{MPa}}"
            )
            st.latex(
                rf"\sigma_{{eq}} = \sqrt{{\sigma_n^2 + 3\tau^2}}"
                rf" = \sqrt{{{sigma_n:.2f}^2 + 3 \times {tau:.2f}^2}} = {sigma_eq:.2f}\ \text{{MPa}}"
            )
            st.latex(
                rf"\text{{Utilisation}} = \frac{{\sigma_{{eq}}}}{{f_{{yk}}/1.5}}"
                rf" = \frac{{{sigma_eq:.2f}}}{{{(fyk/1.5):.1f}}} = {utilisation*100:.1f}\ \%"
            )


# Lancer la page si utilisée directement
if __name__ == "__main__":
    show()

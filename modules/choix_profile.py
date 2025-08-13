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
            h      = float(pick(p, "h"))
            Wel    = float(pick(p, "Wel"))          # cm³
            Avz    = float(pick(p, "Avz"))          # cm²
            Iv     = pick(p, "Iv", "Iy")            # cm⁴ (optionnel)
            Iv     = None if Iv in (None, "None", "") else float(Iv)
            poids  = float(pick(p, "Poids", "masse"))
            typ    = str(pick(p, "type"))

            b      = float(pick(p, "b",  default=0.0))
            tw     = float(pick(p, "tw", default=0.0))
            tf     = float(pick(p, "tf", default=0.0))
            r      = float(pick(p, "r",  default=0.0))
            A      = float(pick(p, "A",  default=0.0))

            if Wel <= 0 or Avz <= 0:
                continue

            cleaned[name] = {
                "h": h, "Wel": Wel, "Avz": Avz, "Iv": Iv,
                "Poids": poids, "type": typ, "b": b, "tw": tw, "tf": tf, "r": r, "A": A
            }
        except Exception as e:
            print(f"⚠️ Profil ignoré ({name}) : {e}")

    return cleaned


# ---------- Calculs ----------
def calcul_contraintes(profile, M, V, fyk):
    Wel_mm3 = profile["Wel"] * 1e3   # cm³ → mm³
    Avz_mm2 = profile["Avz"] * 1e2   # cm² → mm²
    sigma_n = (M * 1e6) / Wel_mm3    # MPa
    tau     = (V * 1e3) / Avz_mm2    # MPa
    sigma_eq = math.sqrt(sigma_n**2 + 3 * tau**2)
    utilisation = sigma_eq / (fyk / 1.5)
    return sigma_n, tau, sigma_eq, utilisation


def fmt_no_trailing_zeros(x, digits=3):
    """Retourne une str sans zéros inutiles après la virgule."""
    if x is None:
        return "—"
    try:
        xf = float(x)
    except Exception:
        return str(x)
    if xf.is_integer():
        return str(int(round(xf)))
    return f"{xf:.{digits}f}".rstrip("0").rstrip(".")


def latex_left(math_block: str):
    """Affiche un bloc LaTeX aligné à gauche."""
    st.markdown(f"<div style='text-align:left'>{math_block}</div>", unsafe_allow_html=True)


# ---------- UI ----------
def show():
    st.title("Choix de profilé métallique optimisé")

    profiles = load_profiles()
    if not profiles:
        st.error("Aucun profil n’a été chargé. Vérifie que **profiles_test.json** existe et contient des clés "
                 "`h`, `Wel`, `Avz`, `masse/Poids`, `type`.")
        return

    familles_disponibles = sorted({p["type"] for p in profiles.values()})
    default_familles = ["HEA"] if "HEA" in familles_disponibles else familles_disponibles[:1]

    # Deux colonnes : le multiselect reste dans la colonne gauche
    col_left, col_right = st.columns([1.35, 1.0])

    with col_left:
        familles_choisies = st.multiselect(
            "Types de profilés à inclure :", options=familles_disponibles, default=default_familles
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            M = st.number_input("M [kN·m]", min_value=0.0, step=10.0, value=0.0)
        with col2:
            V = st.number_input("V [kN]", min_value=0.0, step=10.0, value=0.0)
        with col3:
            acier = st.selectbox("Acier", ["S235", "S275", "S355"], index=0)
        fyk = int(acier[1:])

        Iv_min = st.number_input("Iv min. [cm⁴] (optionnel)", min_value=0.0, step=100.0, value=0.0)

        profils_filtres = (
            {k: v for k, v in profiles.items() if v["type"] in familles_choisies}
            if familles_choisies else profiles
        )

        # Calculs
        rows = []
        for nom, prof in profils_filtres.items():
            if prof["Iv"] is not None and Iv_min > 0 and prof["Iv"] < Iv_min:
                continue
            sigma_n, tau, sigma_eq, utilisation = calcul_contraintes(prof, M, V, fyk)
            rows.append({
                "Utilisation [%]": round(utilisation * 100, 3),
                "Profilé": nom,
                "h [mm]": int(prof["h"]),
                "Wel [cm³]": prof["Wel"],
                "Avz [cm²]": prof["Avz"],
                "Iv [cm⁴]": prof["Iv"],
                "Poids [kg/m]": prof["Poids"],
                "σ [MPa]": sigma_n,
                "τ [MPa]": tau,
                "σeq [MPa]": sigma_eq,
            })

        # Tri par utilisation (par défaut)
        rows = sorted(rows, key=lambda x: x["Utilisation [%]"]) if rows else []

        st.subheader("📌 Profilé optimal :")
        if not rows:
            st.warning("Aucun profilé ne satisfait aux critères.")
            return

        df = pd.DataFrame(rows).set_index("Profilé")

        # Meilleur ≤100%
        best_name = None
        util_series = df["Utilisation [%]"]
        le100 = util_series <= 100.0
        if le100.any():
            best_name = (100.0 - util_series[le100]).idxmin()

        noms = df.index.tolist()
        default_idx = noms.index(best_name) if best_name in noms else 0
        nom_selectionne = st.selectbox("Sélectionner un profilé :", options=noms, index=default_idx)

        # Styles: couleurs + formatage (sans zéros inutiles)
        def _row_style(row):
            u = row["Utilisation [%]"]
            if row.name == best_name:
                color = "#b7f7c1"   # vert soutenu
            elif u <= 100:
                color = "#eafaf0"   # vert pâle
            else:
                color = "#ffeaea"   # rouge pâle
            return [f"background-color: {color}"] * len(row)

        afficher_tous = st.checkbox("Afficher tous les profilés ✓/✗", value=True)
        if afficher_tous:
            st.dataframe(
                df.style.apply(_row_style, axis=1)
                       .format(lambda v: fmt_no_trailing_zeros(v, digits=3)),
                use_container_width=True
            )

    with col_right:
        # Panneau propriétés / formules
        profil = profiles[nom_selectionne]
        st.markdown(f"### {nom_selectionne}")  # sans type entre parenthèses

        # Deux petits tableaux côte à côte (4 colonnes au total)
        c1, c2 = st.columns(2)

        dims = [
            ("h [mm]",  profil["h"]),
            ("b [mm]",  profil["b"]),
            ("tw [mm]", profil["tw"]),
            ("tf [mm]", profil["tf"]),
            ("r [mm]",  profil["r"]),
        ]
        props = [
            ("Poids [kg/m]", profil["Poids"]),
            ("A [cm²]",     profil["A"]),
            ("Wel [cm³]",   profil["Wel"]),
            ("Avz [cm²]",   profil["Avz"]),
            ("Iv [cm⁴]",    profil["Iv"]),
        ]

        with c1:
            st.markdown("**Dimensions**")
            df_dims = pd.DataFrame(
                {"Dimensions": [d[0] for d in dims],
                 "Valeur": [fmt_no_trailing_zeros(d[1]) for d in dims]}
            )
            st.dataframe(df_dims, hide_index=True, use_container_width=True)

        with c2:
            st.markdown("**Propriété**")
            df_props = pd.DataFrame(
                {"Propriété": [p[0] for p in props],
                 "Valeur": [fmt_no_trailing_zeros(p[1]) for p in props]}
            )
            st.dataframe(df_props, hide_index=True, use_container_width=True)

        # Formules (alignées à gauche)
        st.subheader("Formules de dimensionnement")

        sigma_n, tau, sigma_eq, utilisation = calcul_contraintes(profil, M, V, fyk)

        latex_left(
            r"""$$
            \sigma_n = \frac{M \times 10^6}{W_{el} \times 10^3}
            = \frac{""" + f"{M:.1f}" + r""" \times 10^6}{""" + f"{profil['Wel']:.1f}" + r""" \times 10^3}
            = """ + f"{sigma_n:.2f}" + r"""\ \text{MPa}
            $$"""
        )
        latex_left(
            r"""$$
            \tau = \frac{V \times 10^3}{A_{vz} \times 10^2}
            = \frac{""" + f"{V:.1f}" + r""" \times 10^3}{""" + f"{profil['Avz']:.2f}" + r""" \times 10^2}
            = """ + f"{tau:.2f}" + r"""\ \text{MPa}
            $$"""
        )
        latex_left(
            r"""$$
            \sigma_{eq} = \sqrt{\sigma_n^2 + 3\tau^2}
            = \sqrt{""" + f"{sigma_n:.2f}" + r"""^2 + 3 \times """ + f"{tau:.2f}" + r"""^2}
            = """ + f"{sigma_eq:.2f}" + r"""\ \text{MPa}
            $$"""
        )
        latex_left(
            r"""$$
            \text{Utilisation} = \frac{\sigma_{eq}}{f_{yk}/1.5}
            = \frac{""" + f"{sigma_eq:.2f}" + r"""}{""" + f"{(fyk/1.5):.1f}" + r"""}
            = """ + f"{utilisation*100:.1f}" + r"""\ \%
            $$"""
        )


# Lancer la page si utilisée directement
if __name__ == "__main__":
    show()

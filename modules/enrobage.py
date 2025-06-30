import streamlit as st
import math

# --- Données pour le tableau d'exposition ---
exposition_data = [
    {
        "titre": "1 Aucun risque de corrosion ni d’attaque",
        "classes": [
            {
                "code": "X0",
                "description": "Béton non armé ou avec des pièces métalliques noyées : toutes expositions sauf en cas de gel/dégel, d’abrasion et d’attaque chimique.",
                "exemple": "Béton à l’intérieur de bâtiments où le taux d’humidité de l’air ambiant est très faible."
            }
        ]
    },
    {
        "titre": "2 Corrosion induite par carbonatation",
        "classes": [
            {
                "code": "XC1",
                "description": "Sec ou humide en permanence.",
                "exemple": "Béton à l’intérieur de bâtiments où le taux d’humidité de l’air ambiant est faible."
            },
            {
                "code": "XC2",
                "description": "Humide, rarement sec.",
                "exemple": "Béton immergé en permanence dans de l’eau."
            },
            {
                "code": "XC3",
                "description": "Humidité modérée.",
                "exemple": "Béton à l’intérieur de bâtiments où le taux d’humidité de l’air ambiant est élevé."
            },
            {
                "code": "XC4",
                "description": "Alternativement humide et sec.",
                "exemple": "Béton extérieur abrité de la pluie."
            }
        ]
    },
    {
        "titre": "3 Corrosion induite par les chlorures",
        "classes": [
            {
                "code": "XD1",
                "description": "Humidité modérée.",
                "exemple": "Surfaces de béton exposées à des chlorures transportés par voie aérienne."
            },
            {
                "code": "XD2",
                "description": "Humide, rarement sec.",
                "exemple": "Piscines, éléments en béton exposés à des eaux industrielles contenant des chlorures."
            },
            {
                "code": "XD3",
                "description": "Alternativement humide et sec.",
                "exemple": "Éléments de ponts exposés à des projections contenant des chlorures."
            }
        ]
    },
    {
        "titre": "4 Corrosion induite par les chlorures présents dans l’eau de mer",
        "classes": [
            {
                "code": "XS1",
                "description": "Exposé à l’air véhiculant du sel marin mais pas en contact direct avec l’eau de mer.",
                "exemple": "Structures sur ou à proximité d’une côte."
            },
            {
                "code": "XS2",
                "description": "Immergé en permanence.",
                "exemple": "Éléments de structures marines."
            },
            {
                "code": "XS3",
                "description": "Zones de marnage, zones soumises à des projections ou à des embruns.",
                "exemple": "Éléments de structures marines."
            }
        ]
    }
]

classe_structurale_defaults = {
    "X0": "S1", "XC1": "S2", "XC2": "S4", "XC3": "S4", "XC4": "S5",
    "XD1": "S5", "XD2": "S5", "XD3": "S5",
    "XS1": "S5", "XS2": "S5", "XS3": "S6"
}

valeurs_cmin_dur = {
    "S1": [10], "S2": [10], "S3": [15],
    "S4": [20], "S5": [25], "S6": [30]
}

# --- Fonction principale ---
def show():
    st.title("🧱 Calcul de l'enrobage du béton")
    col_form, col_result = st.columns([1.2, 1])

    with col_form:
        st.header("Entrée des données")
        st.subheader("🔹 Paramètres généraux")

        type_element = st.selectbox("Type d'élément", ["Poutre", "Poteau", "Dalle", "Voile"])
        position = st.selectbox("Position dans l’ouvrage", ["Intérieur", "Extérieur"])

        classe_exposition = None
        for groupe in exposition_data:
            with st.expander(groupe["titre"], expanded=False):
                for classe in groupe["classes"]:
                    label = f"{classe['code']} — {classe['description']} \n *Ex: {classe['exemple']}*"
                    if st.button(label, key=classe["code"]):
                        classe_exposition = classe["code"]

        if not classe_exposition:
            st.warning("Veuillez sélectionner une classe d’exposition dans les onglets ci-dessus.")
            return

        classe_structurale = st.selectbox("Classe structurale", list(valeurs_cmin_dur.keys()),
                                          index=list(valeurs_cmin_dur.keys()).index(classe_structurale_defaults[classe_exposition]))

        diametre_armature = st.number_input("Diamètre max des armatures [mm]", value=20, step=1, min_value=6)
        tolerance_constructive = st.radio("Tolérance constructive", [10, 7], index=0)

        st.subheader("🔹 Paramètres feu")
        check_feu = st.checkbox("Vérifier la résistance au feu")
        if check_feu:
            st.info("🔒 À venir dans la prochaine mise à jour.")

    with col_result:
        st.header("Résultats")

        c_min_dur = valeurs_cmin_dur[classe_structurale][0]
        c_min_b = diametre_armature
        delta_c_dev = tolerance_constructive

        c_min = max(c_min_b, c_min_dur)
        c_nom = c_min + delta_c_dev

        st.subheader("🔹 Section A – Enrobage pour durabilité")
        st.markdown(f"- **c_min,dur** : {c_min_dur} mm")
        st.markdown(f"- **c_min,b** : {c_min_b} mm")
        st.markdown(f"- **Δc_dev** : {delta_c_dev} mm")
        st.markdown(f"- **c_nom,durabilité** = {c_nom} mm")

        st.subheader("🔹 Section B – Enrobage pour résistance au feu")
        if not check_feu:
            st.markdown("- Non requis")
        else:
            st.markdown("- 🔒 *À venir dans la prochaine mise à jour*")

        st.subheader("🔹 Section C – Résumé final")
        st.markdown(f"- **Enrobage requis** = {c_nom} mm")

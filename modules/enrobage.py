import streamlit as st
import math

# --- Données pour le tableau d'exposition complet avec info-bulle ---
exposition_data = [
    # Aucun risque
    {"groupe": "Aucun risque de corrosion ni d’attaque", "classe": "X0", "description": "Béton non armé et sans pièces métalliques noyées : toutes expositions sauf en cas de gel/dégel, d’abrasion et d’attaque chimique", "exemple": "Béton à l’intérieur de bâtiments où le taux d’humidité de l’air ambiant est très faible"},

    # Carbonatation
    {"groupe": "Corrosion induite par carbonatation", "classe": "XC1", "description": "Sec ou humide en permanence", "exemple": "Béton à l’intérieur de bâtiments ou le taux d’humidité de l’air ambiant est faible"},
    {"groupe": "Corrosion induite par carbonatation", "classe": "XC2", "description": "Humide, rarement sec", "exemple": "Surfaces de béton soumises au contact à long terme de l’eau"},
    {"groupe": "Corrosion induite par carbonatation", "classe": "XC3", "description": "Humidité modérée", "exemple": "Béton à l’intérieur de bâtiments où le taux d’humidité de l’air ambiant est moyennement élevé"},
    {"groupe": "Corrosion induite par carbonatation", "classe": "XC4", "description": "Alternativement humide et sec", "exemple": "Béton extérieur abrité de la pluie"},

    # Chlorures non marins
    {"groupe": "Corrosion induite par les chlorures (non marins)", "classe": "XD1", "description": "Humidité modérée", "exemple": "Surfaces de béton exposées à des chlorures transportés par voie aérienne"},
    {"groupe": "Corrosion induite par les chlorures (non marins)", "classe": "XD2", "description": "Humide, rarement sec", "exemple": "Piscines, éléments en béton exposés à des eaux industrielles contenant des chlorures"},
    {"groupe": "Corrosion induite par les chlorures (non marins)", "classe": "XD3", "description": "Alternativement humide et sec", "exemple": "Éléments de ponts exposés à des projections contenant des chlorures, chaussées, parkings"},

    # Chlorures marins
    {"groupe": "Corrosion induite par les chlorures (eau de mer)", "classe": "XS1", "description": "Exposé à l’air véhiculant du sel marin mais pas en contact direct avec l’eau de mer", "exemple": "Structures sur ou à proximité d’une côte"},
    {"groupe": "Corrosion induite par les chlorures (eau de mer)", "classe": "XS2", "description": "Immergé en permanence", "exemple": "Éléments de structures marines"},
    {"groupe": "Corrosion induite par les chlorures (eau de mer)", "classe": "XS3", "description": "Zones de marnage, zones soumises à des projections ou à des embruns", "exemple": "Éléments de structures marines"},
]

# Structure pour menu déroulant
groupes = sorted(set([row["groupe"] for row in exposition_data]))
options = []
tooltips = {}

for groupe in groupes:
    for item in [row for row in exposition_data if row["groupe"] == groupe]:
        label = f"{item['classe']} – {item['description']}"
        options.append(label)
        tooltips[label] = f"{item['description']}\n\n*Exemple :* _{item['exemple']}_"

# --- Données d'enrobage ---
classe_structurale_defaults = {
    "X0": "S1", "XC1": "S2", "XC2": "S4", "XC3": "S4", "XC4": "S5",
    "XD1": "S5", "XD2": "S5", "XD3": "S5", "XS1": "S5", "XS2": "S5", "XS3": "S6"
}

valeurs_cmin_dur = {
    "S1": [10]*11,
    "S2": [10, 10, 15, 15, 20, 25, 30, 30, 30, 30, 30],
    "S3": [15]*11,
    "S4": [20]*11,
    "S5": [25]*11,
    "S6": [30]*11
}

# --- Interface utilisateur ---
st.title("🧱 Calcul de l'enrobage du béton")
col_form, col_result = st.columns([1.2, 1])

with col_form:
    st.header("Entrée des données")
    st.subheader("🔹 Paramètres généraux")

    type_element = st.selectbox("Type d'élément", ["Poutre", "Poteau", "Dalle", "Voile"])
    position = st.selectbox("Position dans l’ouvrage", ["Intérieur", "Extérieur"])
    selected_label = st.selectbox("Classe d’exposition", options, format_func=lambda x: x.split(" – ")[0])
    classe_exposition = selected_label.split(" – ")[0]

    classe_structurale = st.selectbox("Classe structurale", list(valeurs_cmin_dur.keys()),
                                      index=list(valeurs_cmin_dur.keys()).index(classe_structurale_defaults.get(classe_exposition, "S1")))

    diametre_armature = st.number_input("Diamètre max des armatures [mm]", value=20, step=1, min_value=6)
    tolerance_constructive = st.radio("Tolérance constructive", [10, 7], index=0)

    st.subheader("🔹 Paramètres feu")
    check_feu = st.checkbox("Vérifier la résistance au feu")
    if check_feu:
        st.info("🔒 A venir dans la prochaine mise à jour.")

# --- Résultats ---
with col_result:
    st.header("Résultats")

    idx = [item['classe'] for item in exposition_data].index(classe_exposition)
    c_min_dur = valeurs_cmin_dur[classe_structurale][idx]
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

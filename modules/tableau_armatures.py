import streamlit as st
import pandas as pd

def show():
    # --- Titre + bouton Accueil ---
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("## 📊 Tableau des sections d’armatures")
    with col2:
        if st.button("🏠 Accueil", key="retour_accueil_armatures"):
            st.session_state.page = "Accueil"

    st.markdown("---")

    # --- Données du tableau ---
    diametres = [6, 8, 10, 12, 14, 16, 20, 25, 28, 30, 32, 40]
    poids = [0.222, 0.395, 0.617, 0.889, 1.210, 1.580, 2.469, 3.858, 4.840, 5.556, 6.321, 9.877]

    tableau_data = {
        "Ø (mm)": diametres,
        "1 barre": [28, 50, 79, 113, 154, 201, 314, 491, 616, 707, 804, 1257],
        "2 barres": [57, 101, 157, 226, 308, 402, 628, 982, 1232, 1414, 1608, 2513],
        "3 barres": [85, 151, 236, 339, 462, 603, 942, 1473, 1847, 2121, 2413, 3770],
        "4 barres": [113, 201, 314, 452, 616, 804, 1257, 1963, 2463, 2827, 3217, 5027],
        "5 barres": [141, 251, 393, 565, 770, 1005, 1571, 2454, 3079, 3534, 4021, 6283],
        "6 barres": [170, 302, 471, 679, 924, 1206, 1885, 2945, 3695, 4241, 4825, 7540],
        "7 barres": [198, 352, 550, 792, 1078, 1407, 2199, 3436, 4310, 4948, 5630, 8796],
        "8 barres": [226, 402, 628, 905, 1232, 1608, 2513, 3927, 4926, 5655, 6434, 10053],
        "9 barres": [254, 452, 707, 1018, 1385, 1810, 2827, 4418, 5542, 6362, 7238, 11310],
        "10 barres": [283, 503, 785, 1131, 1539, 2011, 3142, 4909, 6158, 7069, 8042, 12566],
        "Poids (kg/m)": poids,
        "Poids (kg/m³)": [round(p * 7860, 0) for p in poids]
    }

    df = pd.DataFrame(tableau_data)

    # --- Affichage ---
    st.dataframe(df.style.format(precision=0), use_container_width=True)

import streamlit as st
from PIL import Image
import os

def show():
    st.markdown("<h1 style='text-align: center;'>Études Structure</h1>", unsafe_allow_html=True)
    st.markdown("## 🧱 Béton")

    image_dir = "assets"  # dossier contenant les images

    beton_tools = [
        {"image": "Logo_poutre.png", "label": "Poutre", "page": "Poutre"},
        {"image": "Logo_dalle.png", "label": "Dalle", "page": "Dalle"},
        {"image": "Tableau armature.png", "label": "Tableau armatures", "page": "Tableau armatures"},
        {"image": "Recouvrement.png", "label": "Recouvrement", "page": "Recouvrement"},
    ]

    cols = st.columns(4)
    for i, tool in enumerate(beton_tools):
        with cols[i]:
            st.image(os.path.join(image_dir, tool["image"]), use_column_width="always")
            if st.button(tool["label"], key=f"beton_{tool['label']}"):
                st.session_state.page = tool["page"]

    st.markdown("---")
    st.markdown("## 🏗️ Acier")

    acier_tools = [
        {"image": "Profilé_métallique.png", "label": "Profilé métallique", "page": "Profilé métallique"},
        {"image": "Choix_profilé.png", "label": "Choix profilé", "page": "Choix profilé"},
        {"image": "Flambement.png", "label": "Flambement", "page": "Flambement"},
        {"image": "Tableau_profils.png", "label": "Tableau profilés", "page": "Tableau profilés"},
    ]

    cols = st.columns(4)
    for i, tool in enumerate(acier_tools):
        with cols[i]:
            st.image(os.path.join(image_dir, tool["image"]), use_column_width="always")
            if st.button(tool["label"], key=f"acier_{tool['label']}"):
                st.session_state.page = tool["page"]

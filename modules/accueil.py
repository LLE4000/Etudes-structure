import streamlit as st
import os

def show():
    st.markdown("<h1 style='text-align: center;'>Études Structure</h1>", unsafe_allow_html=True)

    image_dir = "assets"

    # Section Béton
    st.markdown("## 🧱 <span style='color:#FF6F61;'>Béton</span>", unsafe_allow_html=True)
    beton_tools = [
        {"image": "Logo_poutre.png", "label": "Poutre", "page": "Poutre"},
        {"image": "Logo_dalle.png", "label": "Dalle", "page": "Dalle"},
        {"image": "Logo_poutre.png", "label": "Tableau armatures", "page": "Tableau armatures"},
        {"image": "Logo_poutre.png", "label": "Recouvrement", "page": "Recouvrement"},
    ]

    cols = st.columns(4)
    for i, tool in enumerate(beton_tools):
        with cols[i]:
            image_path = os.path.join(image_dir, tool["image"])
            if os.path.exists(image_path):
                st.image(image_path, width=80)
            else:
                st.warning(f"Image manquante : {tool['image']}")
            if st.button(tool["label"], key=f"btn_{tool['label']}"):
                st.session_state.page = tool["page"]
                st.experimental_rerun()

    st.markdown("---")

    # Section Acier
    st.markdown("## 🏗️ <span style='color:#FFA500;'>Acier</span>", unsafe_allow_html=True)
    acier_tools = [
        {"image": "Logo_poutre.png", "label": "Profilé métallique", "page": "Profilé métallique"},
        {"image": "Logo_poutre.png", "label": "Choix profilé", "page": "Choix profilé"},
        {"image": "Logo_poutre.png", "label": "Flambement", "page": "Flambement"},
        {"image": "Logo_poutre.png", "label": "Tableau profilés", "page": "Tableau profilés"},
    ]

    cols = st.columns(4)
    for i, tool in enumerate(acier_tools):
        with cols[i]:
            image_path = os.path.join(image_dir, tool["image"])
            if os.path.exists(image_path):
                st.image(image_path, width=80)
            else:
                st.warning(f"Image manquante : {tool['image']}")
            if st.button(tool["label"], key=f"btn_{tool['label']}"):
                st.session_state.page = tool["page"]
                st.experimental_rerun()

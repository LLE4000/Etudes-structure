import streamlit as st
import os

def show():
    st.markdown("<h1 style='text-align: center;'>Études Structure</h1>", unsafe_allow_html=True)
    st.markdown("## 🧱 Béton")

    image_dir = "assets"

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
            # Création d'un lien cliquable avec l'image
            if st.button("", key=f"img_beton_{i}"):
                st.session_state.page = tool["page"]
            st.image(image_path, use_container_width=True)
            st.markdown(f"<div style='text-align:center'>{tool['label']}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 🏗️ Acier")

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
            if st.button("", key=f"img_acier_{i}"):
                st.session_state.page = tool["page"]
            st.image(image_path, use_container_width=True)
            st.markdown(f"<div style='text-align:center'>{tool['label']}</div>", unsafe_allow_html=True)

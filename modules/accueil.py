import streamlit as st
import os

def clickable_image(image_path, key, page):
    with st.container():
        # On crée un lien cliquable autour de l'image
        button = st.button(
            label="",
            key=key,
            help=page,
            args=(page,),
            on_click=lambda: switch_page(page),
        )
        st.markdown(
            f"""
            <style>
                #{key} {{
                    background-image: url("{image_path}");
                    background-size: contain;
                    background-repeat: no-repeat;
                    background-position: center;
                    height: 100px;
                    width: 100px;
                    border: none;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )

def switch_page(page_name):
    st.session_state.page = page_name
    st.experimental_rerun()

def show():
    st.markdown("<h1 style='text-align: center;'>Études Structure</h1>", unsafe_allow_html=True)
    st.markdown("## 🧱 <span style='color:#FF6F61;'>Béton</span>", unsafe_allow_html=True)

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
            clickable_image(image_path, key=f"img_beton_{i}", page=tool["page"])
            st.markdown(f"<div style='text-align: center;'>{tool['label']}</div>", unsafe_allow_html=True)

    st.markdown("---")
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
            clickable_image(image_path, key=f"img_acier_{i}", page=tool["page"])
            st.markdown(f"<div style='text-align: center;'>{tool['label']}</div>", unsafe_allow_html=True)

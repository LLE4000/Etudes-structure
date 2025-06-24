import streamlit as st

def show():
    st.markdown("<h1 style='text-align: center;'>Études Structure</h1>", unsafe_allow_html=True)

    base_url = "https://raw.githubusercontent.com/LLE4000/Etudes-structure/main/assets"

    def render_section(titre_html, tools):
        st.markdown(titre_html, unsafe_allow_html=True)
        cols = st.columns(4)

        for i, tool in enumerate(tools):
            with cols[i]:
                st.markdown(
                    f"""
                    <div style="text-align: center;">
                        <a href="/?page={tool['page']}" target="_self" style="text-decoration: none;">
                            <img src="{base_url}/{tool['image']}" style="width: 120px; height: 120px; margin-bottom: 8px;" />
                            <div style="font-size: 16px; color: black;">{tool['label']}</div>
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # Outils béton
    beton_tools = [
        {"image": "Logo_poutre.png", "label": "Poutre", "page": "Poutre"},
        {"image": "Logo_dalle.png", "label": "Dalle", "page": "Dalle"},
        {"image": "Logo_poutre.png", "label": "Tableau armatures", "page": "Tableau armatures"},
        {"image": "Logo_poutre.png", "label": "Age beton", "page": "Age beton"},
    ]
    render_section("## 🧱 <span style='color:#FF6F61;'>Béton</span>", beton_tools)

    st.markdown("---")

    # Outils acier
    acier_tools = [
        {"image": "Logo_poutre.png", "label": "Profilé métallique", "page": "Profilé métallique"},
        {"image": "Logo_poutre.png", "label": "Choix profilé", "page": "Choix profilé"},
        {"image": "Logo_poutre.png", "label": "Flambement", "page": "Flambement"},
        {"image": "Logo_poutre.png", "label": "Tableau profilés", "page": "Tableau profilés"},
    ]
    render_section("## 🏗️ <span style='color:#FFA500;'>Acier</span>", acier_tools)

import streamlit as st

def show():
    st.markdown("<h1 style='text-align: center;'>Études Structure</h1>", unsafe_allow_html=True)

    base_url = "https://raw.githubusercontent.com/LLE4000/Etudes-structure/main/assets"

    def render_section(titre_html, tools, cols_per_row=5):
        st.markdown(titre_html, unsafe_allow_html=True)

        for i in range(0, len(tools), cols_per_row):
            ligne_tools = tools[i:i+cols_per_row]
            cols = st.columns(len(ligne_tools))

            for j, tool in enumerate(ligne_tools):
                with cols[j]:
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

    # Outils béton (avec Enrobage en 4ᵉ position)
    beton_tools = [
        {"image": "Logo_poutre.png", "label": "Poutre", "page": "Poutre"},
        {"image": "Logo_dalle.png", "label": "Dalle", "page": "Dalle"},
        {"image": "Logo_age.png", "label": "Age beton", "page": "Age béton"},
        {"image": "Logo_poutre.png", "label": "Enrobage", "page": "Enrobage"},
        {"image": "Logo_poutre.png", "label": "Tableau armatures", "page": "Tableau armatures"},
    ]
    render_section("## 🧱 <span style='color:#FF6F61;'>Béton</span>", beton_tools, cols_per_row=5)

    st.markdown("---")

    # Outils acier (4 éléments)
    acier_tools = [
        {"image": "Logo_poutre.png", "label": "Profilé métallique", "page": "Profilé métallique"},
        {"image": "Logo_poutre.png", "label": "Choix profilé", "page": "Choix profilé"},
        {"image": "Logo_poutre.png", "label": "Flambement", "page": "Flambement"},
        {"image": "Logo_poutre.png", "label": "Tableau profilés", "page": "Tableau profilés"},
    ]
    render_section("## 🏗️ <span style='color:#FFA500;'>Acier</span>", acier_tools, cols_per_row=4)

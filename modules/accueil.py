import streamlit as st

def show():
    st.markdown("<h1 style='text-align: center;'>Études Structure</h1>", unsafe_allow_html=True)

    base_url = "https://raw.githubusercontent.com/LLE4000/Etudes-structure/main/assets"

    # Style CSS pour cartes
    st.markdown("""
        <style>
        .tool-card {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            transition: 0.3s;
        }
        .tool-card:hover {
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            transform: translateY(-3px);
        }
        .tool-container {
            background-color: #f9f9f9;
            border-radius: 15px;
            padding: 20px 10px;
            margin-bottom: 30px;
        }
        </style>
    """, unsafe_allow_html=True)

    def render_section(titre_html, tools, cols_per_row=5):
        st.markdown(f"<div class='tool-container'>{titre_html}", unsafe_allow_html=True)

        for i in range(0, len(tools), cols_per_row):
            ligne_tools = tools[i:i+cols_per_row]
            cols = st.columns(len(ligne_tools))

            for j, tool in enumerate(ligne_tools):
                with cols[j]:
                    st.markdown(
                        f"""
                        <div class="tool-card" style="text-align: center;">
                            <a href="/?page={tool['page']}" target="_self" style="text-decoration: none;">
                                <img src="{base_url}/{tool['image']}" style="width: 100px; height: 100px; margin-bottom: 8px;" />
                                <div style="font-size: 16px; color: black;">{tool['label']}</div>
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.markdown("</div>", unsafe_allow_html=True)

    # ====== LIGNE 1 — Béton ======
    beton_tools = [
        {"image": "Logo_poutre.png", "label": "Poutre", "page": "Poutre"},
        {"image": "Logo_dalle.png", "label": "Dalle", "page": "Dalle"},
        {"image": "Logo_age.png", "label": "Age beton", "page": "Age béton"},
        {"image": "Logo_poutre.png", "label": "Enrobage", "page": "Enrobage"},
        {"image": "Logo_poutre.png", "label": "Tableau armatures", "page": "Tableau armatures"},
    ]
    render_section("## 🧱 <span style='color:#FF6F61;'>Béton</span>", beton_tools, cols_per_row=5)

    # ====== LIGNE 2 — Acier ======
    acier_tools = [
        {"image": "Logo_poutre.png", "label": "Cornière", "page": "Cornière"},
        {"image": "Logo_poutre.png", "label": "Choix profilé", "page": "Choix profilé"},
        {"image": "Logo_poutre.png", "label": "Flambement", "page": "Flambement"},
        {"image": "Logo_poutre.png", "label": "Tableau profilés", "page": "Tableau profilés"},
    ]
    render_section("## 🏗️ <span style='color:#FFA500;'>Acier</span>", acier_tools, cols_per_row=4)

    # ====== LIGNE 3 — Autres ======
    autres_tools = [
        {"image": "Logo_poutre.png", "label": "Garde-corps", "page": "Garde-corps"},
        # Tu pourras ajouter d'autres modules ici
        # {"image": "Logo_xxx.png", "label": "Autre outil", "page": "Nom de page"},
    ]
    render_section("## 🧩 <span style='color:#6C63FF;'>Autres</span>", autres_tools, cols_per_row=4)

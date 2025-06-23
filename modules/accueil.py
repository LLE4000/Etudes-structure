import streamlit as st

def show():
    st.markdown("<h1 style='text-align: center;'>Études Structure</h1>", unsafe_allow_html=True)

    base_url = "https://raw.githubusercontent.com/LLE4000/Etudes-structure/main/assets"

    def render_section(titre_html, tools):
        st.markdown(titre_html, unsafe_allow_html=True)
        cols = st.columns(4)
        for i, tool in enumerate(tools):
            with cols[i]:
                tool_id = f"tool_{tool['page'].replace(' ', '_')}"
                js = f"""
                <script>
                    function click_{tool_id}() {{
                        const streamlitInput = window.parent.document.querySelector('input[data-testid="{tool_id}"]');
                        if (streamlitInput) {{
                            streamlitInput.click();
                        }}
                    }}
                </script>
                """
                st.markdown(
                    f"""
                    <div style="text-align: center;">
                        {js}
                        <img src="{base_url}/{tool['image']}" style="width: 120px; height: 120px; cursor:pointer;" onclick="click_{tool_id}()" />
                        <div style="margin-top: 8px;">{tool['label']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                # Élément caché pour activer le changement de page
                if st.checkbox("", key=tool_id):
                    st.session_state.page = tool["page"]
                    st.experimental_rerun()

    # 🧱 Outils béton
    beton_tools = [
        {"image": "Logo_poutre.png", "label": "Poutre", "page": "Poutre"},
        {"image": "Logo_dalle.png", "label": "Dalle", "page": "Dalle"},
        {"image": "Logo_poutre.png", "label": "Tableau armatures", "page": "Tableau armatures"},
        {"image": "Logo_poutre.png", "label": "Recouvrement", "page": "Recouvrement"},
    ]
    render_section("## 🧱 <span style='color:#FF6F61;'>Béton</span>", beton_tools)

    st.markdown("---")

    # 🏗️ Outils acier
    acier_tools = [
        {"image": "Logo_poutre.png", "label": "Profilé métallique", "page": "Profilé métallique"},
        {"image": "Logo_poutre.png", "label": "Choix profilé", "page": "Choix profilé"},
        {"image": "Logo_poutre.png", "label": "Flambement", "page": "Flambement"},
        {"image": "Logo_poutre.png", "label": "Tableau profilés", "page": "Tableau profilés"},
    ]
    render_section("## 🏗️ <span style='color:#FFA500;'>Acier</span>", acier_tools)

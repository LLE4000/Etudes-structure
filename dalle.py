import streamlit as st

def show():
    st.title("Dalle en béton armé")
    if st.button("🔄 Réinitialiser"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    M = st.number_input("Moment (kNm)", key="dalle_moment")
    V = st.number_input("Effort tranchant (kN)", key="dalle_effort")
    st.write("Moment =", M, "| Effort =", V)

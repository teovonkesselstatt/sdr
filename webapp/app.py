from webapp import weights, references, weights2
import streamlit as st

def run_app():
    st.title('Emerging SDRs')
    PAGES = {
            "Weights": weights,
            "Weights2": weights2,
            "References": references
        }

    st.sidebar.title('Navigation')
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))
    page = PAGES[selection]

    page.run_app()
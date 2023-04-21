from webapp import weights, references
import streamlit as st

def run_app():
    st.title('Real Exchange Rate')
    PAGES = {
            "Weights": weights,
            "References": references
        }

    st.sidebar.title('Navigation')
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))
    page = PAGES[selection]

    page.run_app()
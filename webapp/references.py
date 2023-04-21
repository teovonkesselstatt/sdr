import streamlit as st


def run_app():

    st.title('References')
    st.write("""
    * Nominal Exchange Rate data:
        * http://stats.bis.org:8089/statx/srs/table/I3?c=&p=202302&m=E&f=xlsx
    * IMF Plans: scraped from
        * https://www.imf.org/external/np/fin/tad/extarr1.aspx
    """
    )

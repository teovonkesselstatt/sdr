import streamlit as st


def run_app():

    st.title('References')
    st.write("""
    * Nominal Exchange Rate data:
        * http://stats.bis.org:8089/statx/srs/table/I3?c=&p=202302&m=E&f=xlsx
    * IMF Plans: scraped from
        * https://www.imf.org/external/np/fin/tad/extarr1.aspx
    * Nominal Exchange Rate (daily):
        * https://www.bis.org/statistics/full_data_sets.htm
    * GDP (quarterly):
        * https://data.imf.org/regular.aspx?key=63122827
        * https://data.imf.org/?sk=4c514d48-b6ba-49ed-8ab9-52b0c1a0179b&sId=1390030341854
    """
    )

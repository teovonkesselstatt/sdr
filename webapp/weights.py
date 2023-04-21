import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.cm
import matplotlib.pyplot as plt
import numpy as np
import datetime


def run_app():

    # Read the CSV file into a pandas dataframe
    df_neer = pd.read_csv('data/NEER_m.csv', header=0)
    df_neer.drop(['FREQ','Frequency','COLLECTION','Collection','UNIT_MULT',
                'Unit Multiplier','DECIMALS', 'Decimals', 'Availability',
                'AVAILABILITY', 'TITLE', 'Series'], axis=1, inplace=True)

    # Wide to long
    df_neer = pd.melt(df_neer, id_vars = ['Reference area','REF_AREA','CURRENCY','Currency'], value_vars=df_neer.columns[4:], var_name='Time', value_name='XR')
    df_neer['Time'] = pd.to_datetime(df_neer['Time'], format='%Y-%m')
    df_neer['Time'] = df_neer['Time'].dt.to_period('M').dt.to_timestamp(how='end')
    df_neer['Time'] = df_neer.Time.dt.date

    # Long to wide
    wide_df = df_neer.pivot_table(index='Time', columns='Currency', values='XR')

    ### Abro el df de los planes del FMI
    df_plans = pd.read_csv('data/IMF.csv', header=0)
    df_plans['Date of Arrangement'] = pd.to_datetime(df_plans['Date of Arrangement'], format='%Y-%m-%d')
    df_plans['Date of Arrangement'] = df_plans['Date of Arrangement'].dt.date
    df_plans['Expiration Date'] = pd.to_datetime(df_plans['Expiration Date'], format='%Y-%m-%d')
    df_plans['Expiration Date'] = df_plans['Expiration Date'].dt.date

    # Me quedo con los planes post 2000, pero que terminan pre 2023
    dia1 = datetime.date(2000,1,31)
    dia2 = datetime.date(2023,2,28)
    df_plans = df_plans[(df_plans['Date of Arrangement'] >= dia1) & (df_plans['Expiration Date'] <= dia2)]

    # Change variable types
    df_plans['Amount Agreed'] = pd.to_numeric(df_plans['Amount Agreed'])
    df_plans['Amount Drawn'] = pd.to_numeric(df_plans['Amount Drawn'])

    # Creo las variables que te dicen el ultimo día del mes anterior
    df_plans['Arrangement-1'] = df_plans['Date of Arrangement'] + pd.DateOffset(months = -1)
    df_plans['Arrangement-1'] = df_plans['Arrangement-1'].dt.to_period('M').dt.to_timestamp(how='end')
    df_plans['Arrangement-1'] = df_plans['Arrangement-1'].dt.date

    df_plans['Expiration-1'] = df_plans['Expiration Date'] + pd.DateOffset(months = -1)
    df_plans['Expiration-1'] = df_plans['Expiration-1'].dt.to_period('M').dt.to_timestamp(how='end')
    df_plans['Expiration-1'] = df_plans['Expiration-1'].dt.date

    ## Columna value en USD al principio
    def calculate_amount_usd(row):
        start_date = row['Arrangement-1']
        price_at_start_date = wide_df[((wide_df.index == start_date))]['Special drawing right'].values[0]
        amount = row['Amount Agreed']
        amount_usd = amount / price_at_start_date
        return amount_usd

    df_plans['Start USD'] = df_plans.apply(calculate_amount_usd, axis=1)

    ## Column of value in USD at end
    def calculate_amount2_usd(row):
        end_date = row['Expiration-1']
        price_at_end_date = wide_df[((wide_df.index == end_date))]['Special drawing right'].values[0]
        amount = row['Amount Agreed']
        amount_usd = amount / price_at_end_date
        return amount_usd

    df_plans['End USD'] = df_plans.apply(calculate_amount2_usd, axis=1)

    # Columna de retorno del SDR
    df_plans['Return SDR'] = df_plans['End USD'] / df_plans['Start USD']

    ############################ WEIGHTS ######################################

    weights = {currency: 0 for currency in wide_df.columns}

    weights['Brazilian real'] = st.slider('Brazilian Real', 0, 1, 0)
    weights['Indian rupee'] = st.slider('Indian rupee', 0, 1, 0)
    weights['Russian rouble'] = st.slider('Russian rouble', 0, 1, 0)
    weights['Renminbi'] = st.slider('Renminbi', 0, 1, 0)
    weights['South African Rand'] = st.slider('South African Rand', 0, 1, 0)
    weights['US dollar'] = st.slider('US dollar', 0, 1, 1)
    weights['Egyptian pound'] = st.slider('Egyptian pound', 0, 1, 0)
    weights['Rupiah'] = st.slider('Indonesian Rupiah', 0, 1, 0)  # Indonesia
    weights['Mexican peso'] = st.slider('Mexican peso', 0, 1, 0)
    weights['Saudi riyal'] = st.slider('Saudi riyal', 0, 1, 0)
    weights['Turkish lira'] = st.slider('Turkish lira', 0, 1, 0)


    # Columna del valor del Emerging SDR

    def calculate_emerging(row):
        sum = 0
        for curr in weights:
            if not np.isnan(row[curr]): sum = sum + row[curr]*weights[curr]
        return sum

    wide_df['Emerging SDR'] = wide_df.apply(calculate_emerging, axis=1)

    # Columna value EMERGING en USD al principio
    def calculate_emerging_usd(row):
        start_date = row['Arrangement-1']
        price_at_start_date = wide_df[((wide_df.index == start_date))]['Emerging SDR'].values[0]
        amount = row['Amount Agreed']
        amount_usd = amount / price_at_start_date
        return amount_usd

    df_plans['Start EMERGING USD'] = df_plans.apply(calculate_emerging_usd, axis=1)

    # Columna value EMERGING en USD al final
    def calculate_emerging2_usd(row):
        end_date = row['Expiration-1']
        price_at_end_date = wide_df[((wide_df.index == end_date))]['Emerging SDR'].values[0]
        amount = row['Amount Agreed']
        amount_usd = amount / price_at_end_date
        return amount_usd

    df_plans['End EMERGING USD'] = df_plans.apply(calculate_emerging2_usd, axis=1)

    # Columna de retorno del SDR
    df_plans['Return EMERGING SDR'] = df_plans['End EMERGING USD'] / df_plans['Start EMERGING USD']

    df_display = df_plans[['Country','Facility','Date of Arrangement', 'Expiration Date', 'Return EMERGING SDR','Return SDR']]
    st.dataframe(df_display)
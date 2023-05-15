import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.cm
import matplotlib.pyplot as plt
import numpy as np
import datetime


def run_app():

    # CSV de Flows
    df_flows = pd.read_csv('data/FLOWS.csv', header=9)

    # Me quedo solo con EFF y SBA
    df_flows = df_flows[(df_flows['Description'] == 'Extended Fund Facility') | (df_flows['Description'] == 'Stand-By Arrangement')]
    df_flows = df_flows[(df_flows['Original Arrangement Date'] != 'n.a.')] # Los que elimina son pre 2000 asi que todo bien

    # Paso a los tipos de data que necesito
    df_flows['Transaction Value Date'] = pd.to_datetime(df_flows['Transaction Value Date'], format='%m/%d/%Y')
    df_flows['Original Disbursement Date'] = pd.to_datetime(df_flows['Original Disbursement Date'], format='%m/%d/%Y')
    df_flows['Original Arrangement Date'] = pd.to_datetime(df_flows['Original Arrangement Date'], format='%m/%d/%Y')
    df_flows['Amount'] = pd.to_numeric(df_flows['Amount'])

    # Me quedo con los planes siglo XXI
    dia1 = datetime.date(2000,1,1)
    df_flows = df_flows[(df_flows['Original Arrangement Date'].dt.date >= dia1)]

    # CSV de GDP
    df_gdp = pd.read_csv('data/GDPreal.csv', header=6, na_values='...')
    df_gdp = df_gdp.drop('Unnamed: 0', axis=1)
    df_gdp = pd.melt(df_gdp, id_vars = ['Country'], value_vars=df_gdp.columns[3:], var_name='Time', value_name='Real GDP')
    df_gdp['Real GDP'] = df_gdp['Real GDP'].str.replace(',','').apply(pd.to_numeric)
    df_gdp['Time'] = df_gdp['Time'].str.replace(r'(\d{4})Q', r'\1-Q')
    df_gdp['Time'] = pd.PeriodIndex(df_gdp['Time'], freq='Q').to_timestamp(how = 'end')
    df_gdp['Time'] = df_gdp['Time'].dt.date

    # CSV de Nominal Exchange Rate
    df_daily = pd.read_csv('data/NEER_d.csv', header=0)

    df_daily.drop(['FREQ','Frequency','COLLECTION','Collection','UNIT_MULT',
                'Unit Multiplier','DECIMALS', 'Decimals', 'Availability',
                'AVAILABILITY', 'TITLE', 'Series'], axis=1, inplace=True)

    df_daily = pd.melt(df_daily, id_vars = ['Reference area','REF_AREA','CURRENCY','Currency'], value_vars=df_daily.columns[18000:], var_name='Time', value_name='XR')
    df_daily['Time'] = pd.to_datetime(df_daily['Time'], format='%Y-%m-%d')

    # Creo el wide dataframe con las monedas
    wide_df = df_daily.pivot_table(index='Time', columns='Currency', values='XR')

    # Me quedo con las monedas que me interesan
    wide_df = wide_df[['Brazilian real', 'Chilean peso','Euro','Hong Kong dollar',
                    'Indian rupee','Mexican peso','Pound (sterling)','Renminbi',
                    'Rupiah','Russian rouble','Saudi riyal','Singapore dollar',
                    'South African Rand','Special drawing right',
                        'Turkish lira','US dollar','Yen']]

    # Elimino las primeras dos filas, que tienen algunos NAs
    wide_df = wide_df.iloc[2:]
    wide_df = wide_df.interpolate()

    ############################ WEIGHTS ######################################

    weights = {currency: 0 for currency in wide_df.columns}

    if st.button('Reset Values'):
        for currency in wide_df.columns:
            weights[currency] = st.slider('##### ' + currency, min_value=0.0, max_value=1.0, value=0.0, step=0.01)


    # Columna del valor del Emerging SDR

    def calculate_emerging(row):
        sum = 0
        for curr in weights:
            if not np.isnan(row[curr]): sum = sum + row[curr]*weights[curr]
        return sum

    wide_df['Emerging SDR'] = wide_df.apply(calculate_emerging, axis=1)

    # Limito a un solo plan
    country = st.sidebar.selectbox(
        'Select a country',
        df_flows['Member'].unique())


    # Veo caso de un país
    df_country = df_flows[(df_flows['Member'] == country)].sort_values('Transaction Value Date')

    # Lista de planes del país
    planes_country = df_country['Original Arrangement Date'].unique()

    nro_plan = st.sidebar.selectbox(
        'Select a plan',
        planes_country)


    # Me limito solo al plan elegido
    plan = df_country[(df_country['Original Arrangement Date'] == nro_plan)]

    # Lo pongo en terminos de deuda (postivo es que le debo al FMI)
    plan.loc[plan['Flow Type'] == 'GRA Repurchases', 'Amount'] = -1 * plan['Amount']

    plan.loc[:,'Debt'] = plan.Amount.cumsum()

    # Column of value in USD for SDR and Emerging SDR

    def calculate_amount_currency(row,currency):
        end_date = row['Transaction Value Date']
        price_at_date = wide_df[((wide_df.index == end_date))][currency].values[0]
        amount = row['Amount'] * (-1)
        amount = amount / price_at_date
        return amount


    plan.loc[:,'Amount SDR'] = plan.apply(calculate_amount_currency, currency='Special drawing right', axis=1)
    plan.loc[:,'Amount EMR'] = plan.apply(calculate_amount_currency, currency='Emerging SDR', axis=1)

    # Me limito a un solo pais, un solo plan
    df_gdp_country = df_gdp[df_gdp['Country'] == country]

    # Calcula la suma de pagos de capital en cada trimestre
    def calculate_imf_sdr(row, currency):
        date = row['Time']
        amount = plan.loc[(plan['Transaction Value Date'].dt.date <= date ) &
            (plan['Transaction Value Date'].dt.date > date - pd.DateOffset(months = 3)) &
            (plan['Flow Type'] == 'GRA Repurchases'),
            currency].sum()
        return amount

    df_gdp_country['IMF Payment SDR'] = df_gdp_country.apply(calculate_imf_sdr, currency='Amount SDR', axis=1)
    df_gdp_country['IMF Payment EMR'] = df_gdp_country.apply(calculate_imf_sdr, currency='Amount EMR', axis=1)

    # Guardo el valor que SDR y EMR tenian cuando se acordo el plan
    sdr = wide_df[(wide_df.index == nro_plan)]['Special drawing right'][0]
    emr = wide_df[(wide_df.index == nro_plan)]['Emerging SDR'][0]

    # Ajusto los valores de los pagos como para que el monto en dolares arranque siendo igual
    df_gdp_country['IMF Payment EMR'] = df_gdp_country['IMF Payment EMR'] / sdr * emr


    fig1, ax1 = plt.subplots(figsize=(12, 4))

    df_gdp_country.plot(x = "Time", \
            y = ["IMF Payment SDR","IMF Payment EMR"], \
                style=['-','-'], \
                    color=['r','b'],\
                        ax = ax1)

    df_gdp_country.plot('Time','Real GDP',secondary_y=True, ax=ax1)

    st.pyplot(fig1)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from sqlalchemy import create_engine

# Configuration de la page (doit être la première commande Streamlit)
st.set_page_config(page_title="Tableau de Bord Météorologique", layout="wide")

# Configuration de la connexion à la base de données
DATABASE_URL = "mysql+pymysql://phpmyadmin:bah@localhost/data_warehouse"

# Fonction pour charger les données
@st.cache_data
def load_data():
    engine = create_engine(DATABASE_URL)
    query = """
    SELECT cd.*, c.name as country_name, dd.date
    FROM climate_data cd 
    JOIN countries c ON cd.country_id = c.id
    JOIN date_dimension dd ON cd.date_id = dd.id
    """
    df = pd.read_sql(query, engine)
    df['date'] = pd.to_datetime(df['date'])
    return df

# Chargement des données
df = load_data()

# Titre
st.title("Tableau de Bord Météorologique")

# Sidebar pour les filtres
st.sidebar.header("Filtres")
country = st.sidebar.selectbox("Sélectionnez un pays", options=df['country_name'].unique())
date_range = st.sidebar.date_input("Sélectionnez une plage de dates", 
                                   [df['date'].min(), df['date'].max()],
                                   min_value=df['date'].min(),
                                   max_value=df['date'].max())

# Filtrage des données
filtered_df = df[(df['country_name'] == country) & 
                 (df['date'] >= pd.to_datetime(date_range[0])) & 
                 (df['date'] <= pd.to_datetime(date_range[1]))]

# KPI summary
col1, col2, col3, col4 = st.columns(4)
col1.metric("Température moyenne", f"{filtered_df['mean_2m_air_temperature'].mean():.1f}°C")
col2.metric("Précipitations totales", f"{filtered_df['total_precipitation'].sum():.1f} mm")
col3.metric("Pression moyenne", f"{filtered_df['surface_pressure'].mean():.1f} hPa")
wind_speed = np.sqrt(filtered_df['u_component_of_wind_10m']**2 + filtered_df['v_component_of_wind_10m']**2)
col4.metric("Vitesse du vent moyenne", f"{wind_speed.mean():.1f} m/s")

# Graphiques
st.header("Visualisations")

# Graphique de température
fig_temp = go.Figure()
fig_temp.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['mean_2m_air_temperature'],
                              mode='lines', name='Température moyenne'))
fig_temp.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['maximum_2m_air_temperature'],
                              mode='lines', name='Température maximale', line=dict(dash='dash')))
fig_temp.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['minimum_2m_air_temperature'],
                              mode='lines', name='Température minimale', line=dict(dash='dot')))
fig_temp.update_layout(title=f'Températures pour {country}',
                       xaxis_title='Date', yaxis_title='Température (°C)')
st.plotly_chart(fig_temp, use_container_width=True)

# Graphique de précipitations
fig_precip = px.bar(filtered_df, x='date', y='total_precipitation',
                    title=f'Précipitations totales pour {country}')
fig_precip.update_layout(xaxis_title='Date', yaxis_title='Précipitations (mm)')
st.plotly_chart(fig_precip, use_container_width=True)

# Graphique de pression
fig_pressure = go.Figure()
fig_pressure.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['surface_pressure'],
                                  mode='lines', name='Pression de surface'))
fig_pressure.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['mean_sea_level_pressure'],
                                  mode='lines', name='Pression au niveau de la mer'))
fig_pressure.update_layout(title=f'Pression atmosphérique pour {country}',
                           xaxis_title='Date', yaxis_title='Pression (hPa)')
st.plotly_chart(fig_pressure, use_container_width=True)

# Graphique de vent
fig_wind = go.Figure()
fig_wind.add_trace(go.Scatter(x=filtered_df['date'], y=wind_speed, mode='lines', name='Vitesse du vent'))
fig_wind.update_layout(title=f'Vitesse du vent pour {country}',
                       xaxis_title='Date', yaxis_title='Vitesse du vent (m/s)')
st.plotly_chart(fig_wind, use_container_width=True)

# Carte de chaleur des corrélations
st.header("Carte de Chaleur des Corrélations")
corr_df = filtered_df[['mean_2m_air_temperature', 'total_precipitation', 'surface_pressure', 'u_component_of_wind_10m', 'v_component_of_wind_10m']].corr()
fig_heatmap = px.imshow(corr_df, text_auto=True, aspect="auto")
fig_heatmap.update_layout(title="Corrélations entre les variables météorologiques")
st.plotly_chart(fig_heatmap, use_container_width=True)

# Nouvelle section : Préparation aux événements météorologiques et planification quotidienne

st.header("Préparation et Planification")

# Prévisions simples basées sur les données les plus récentes
latest_data = filtered_df.iloc[-1]
temp = latest_data['mean_2m_air_temperature']
precip = latest_data['total_precipitation']
wind = np.sqrt(latest_data['u_component_of_wind_10m']**2 + latest_data['v_component_of_wind_10m']**2)

st.subheader("Prévisions pour aujourd'hui")

# Obtenir la date la plus récente des données filtrées
latest_date = filtered_df['date'].max()

# Afficher la date
st.write(f"Date des prévisions : {latest_date.strftime('%A %d %B %Y')}")

col1, col2, col3 = st.columns(3)
col1.metric("Température", f"{temp:.1f}°C")
col2.metric("Précipitations", f"{precip:.1f} mm")
col3.metric("Vitesse du vent", f"{wind:.1f} m/s")



st.subheader("Conseils pour la journée")

# Conseils basés sur la température
if temp < 10:
    st.write("• Il fait froid aujourd'hui. N'oubliez pas de vous habiller chaudement.")
elif temp > 25:
    st.write("• Il fait chaud. Pensez à bien vous hydrater et à vous protéger du soleil.")
else:
    st.write("• La température est agréable. Profitez-en pour des activités en plein air.")

# Conseils basés sur les précipitations
if precip > 5:
    st.write("• Des précipitations importantes sont prévues. Prenez un parapluie ou un imperméable.")
elif precip > 0:
    st.write("• Quelques averses sont possibles. Un parapluie pourrait être utile.")
else:
    st.write("• Pas de pluie prévue aujourd'hui.")

# Conseils basés sur le vent
if wind > 10:
    st.write("• Le vent est fort. Soyez prudent lors de vos déplacements.")
elif wind > 5:
    st.write("• Une brise modérée est prévue. Idéal pour les activités de plein air.")
else:
    st.write("• Le vent est faible aujourd'hui.")


st.info("Ces prévisions et conseils sont basés sur les données disponibles et sont à titre indicatif. Pour des informations plus précises, consultez les services météorologiques officiels.")

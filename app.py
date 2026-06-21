import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración estética de la página
st.set_page_config(page_title="F1 Tire Analytics", page_icon="🏎️", layout="wide")

st.title("🏎️ F1 Tire Performance Dashboard")
st.markdown("Análisis de degradación de neumáticos basado en telemetría real.")

# Cargar los datos generados por tu script anterior
try:
    df = pd.read_csv('data/norris_laps_barcelona.csv')
    
    # Sidebar para filtros
    st.sidebar.header("Filtros de Carrera")
    selected_stint = st.sidebar.multiselect("Seleccionar Stint", options=df['Stint'].unique(), default=df['Stint'].unique())
    
    # Filtrar dataframe
    df_filtered = df[df['Stint'].isin(selected_stint)]

    # Layout de columnas para métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("Compuesto Principal", df_filtered['Compound'].iloc[0])
    col2.metric("Mejor Vuelta", f"{df_filtered['LapTimeSeconds'].min():.3f}s")
    col3.metric("Vueltas Analizadas", len(df_filtered))

    # Gráfico interactivo de degradación
    st.subheader("Curva de Degradación (Tiempo vs Vida del Neumático)")
    fig = px.scatter(df_filtered, x="TyreLife", y="LapTimeSeconds", 
                     color="Compound", trendline="ols",
                     title="Evolución del Ritmo por Vuelta",
                     labels={"TyreLife": "Vueltas del Neumático", "LapTimeSeconds": "Tiempo (s)"})
    
    st.plotly_chart(fig, use_container_width=True)

    # Mostrar tabla de datos
    with st.expander("Ver datos crudos"):
        st.write(df_filtered)

except FileNotFoundError:
    st.error("❌ No se encontró el archivo de datos. Por favor, ejecuta primero 'scripts/get_f1_data.py'.")
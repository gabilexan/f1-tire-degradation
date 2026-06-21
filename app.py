import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración estética de la página
st.set_page_config(page_title="F1 Tire Analytics", page_icon="🏎️", layout="wide")

st.title("🏎️ F1 Tire Performance Dashboard")
st.markdown("Tire degradation analysis derived from actual racing telemetry.")

# Función auxiliar para formatear segundos a formato de carrera F1 (MM:SS.ms)
def format_lap_time(seconds):
    if pd.isna(seconds):
        return "N/A"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:06.3f}"

# Cargar los datos generados por tu script anterior
try:
    df = pd.read_csv('data/norris_laps_barcelona.csv')
    
    # Sidebar para filtros
    st.sidebar.header("Race Filters")
    selected_stint = st.sidebar.multiselect(
        "Select Stint", 
        options=sorted(df['Stint'].unique()), 
        default=df['Stint'].unique()
    )
    
    # Filtrar dataframe
    df_filtered = df[df['Stint'].isin(selected_stint)]

    # --- MATRIZ DE MÉTRICAS CLAVE (KPIs) ---
    st.markdown("### 📊 Key Performance Indicators")
    
    if not df_filtered.empty:
        # Cálculos dinámicas basados en el filtro
        fastest_lap_raw = df_filtered['LapTimeSeconds'].min()
        avg_lap_time_raw = df_filtered['LapTimeSeconds'].mean()
        max_tire_age = int(df_filtered['TyreLife'].max())
        baseline_compound = df_filtered['Compound'].iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(label="🏎️ Baseline Compound", value=baseline_compound)
        with col2:
            st.metric(label="⏱️ Fastest Lap", value=format_lap_time(fastest_lap_raw))
        with col3:
            st.metric(label="📈 Average Pace", value=format_lap_time(avg_lap_time_raw))
        with col4:
            st.metric(
                label="🔄 Stint Length", 
                value=f"{max_tire_age} Laps",
                help="Maximum tire age analyzed for the selected stint(s)"
            )
    else:
        st.warning("⚠️ Please select at least one Stint in the sidebar.")

    st.markdown("---")

    # --- GRÁFICO INTERACTIVO DE DEGRADACIÓN ---
    if not df_filtered.empty:
        st.subheader("Degradation Curve (Lap Time vs Tire Age)")
        
        fig = px.scatter(
            df_filtered, 
            x="TyreLife", 
            y="LapTimeSeconds", 
            color="Compound", 
            trendline="ols",
            title="Pace Evolution per Lap",
            labels={
                "TyreLife": "Tire Age (Laps)", 
                "LapTimeSeconds": "Lap Time (s)"
            }
        )
        
        # Aplicar el tema oscuro nativo de Plotly para que combine con la estética F1
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    # --- SECCIÓN DE DATOS CRUDOS ---
    with st.expander("Show Raw Data"):
        st.dataframe(df_filtered, use_container_width=True)

except FileNotFoundError:
    st.error("❌ No se encontró el archivo de datos. Por favor, ejecuta primero 'scripts/get_f1_data.py'.")
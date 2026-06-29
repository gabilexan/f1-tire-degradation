import os
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns


# Configuración estética de la página
st.set_page_config(page_title="F1 Tire Analytics", page_icon="🏎️", layout="wide")

# Función auxiliar para formatear segundos a formato de carrera F1 (MM:SS.ms)
def format_lap_time(seconds):
    if pd.isna(seconds):
        return "N/A"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:06.3f}"

# Cargar los datos generados por tu script anterior (Nuevo dataset comparativo)
try:
   # Obtener la ruta absoluta de la raíz del proyecto para evitar fallos de carga
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'f1_barcelona_comparison.csv')
    
    df = pd.read_csv(data_path)
    
    # --- NAVIGATION IN SIDEBAR ---
    st.sidebar.header("Navigation")
    view_mode = st.sidebar.radio(
        "Select View Mode",
        options=["Single Driver Analysis", "Head-to-Head Comparison"]
    )
    st.sidebar.markdown("---")
    
    # --- FILTERS IN SIDEBAR ---
    st.sidebar.header("Race Filters")
    
    # 1. MODO: ANÁLISIS DE LANDO NORRIS (TU APP ORIGINAL)
    if view_mode == "Single Driver Analysis":
        st.title("🏎️ Lando Norris: Tire Degradation Analysis")
        st.markdown("Tire degradation analysis derived from actual racing telemetry.")
        
        # Forzar datos solo de Lando
        df_norris = df[df['Driver'] == 'Lando Norris']
        
        selected_stint = st.sidebar.multiselect(
            "Select Stint", 
            options=sorted(df_norris['Stint'].unique()), 
            default=df_norris['Stint'].unique()
        )
        
        df_filtered = df_norris[df_norris['Stint'].isin(selected_stint)]

        # --- MATRIZ DE MÉTRICAS CLAVE (KPIs) ---
        st.markdown("### 📊 Key Performance Indicators")
        
        if not df_filtered.empty:
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
            
            st.markdown("---")

            # --- GRÁFICO INTERACTIVO DE DEGRADACIÓN ---
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
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            # --- SECCIÓN DE DATOS CRUDOS ---
            with st.expander("Show Raw Data"):
                st.dataframe(df_filtered, use_container_width=True)
        else:
            st.warning("⚠️ Please select at least one Stint in the sidebar.")

    # 2. MODO: COMPARATIVA NORRIS VS VERSTAPPEN (NUEVA SECCIÓN)
    # 2. MODO: COMPARATIVA NORRIS VS VERSTAPPEN (NUEVA SECCIÓN)
    elif view_mode == "Head-to-Head Comparison":
        st.title("⚔️ Driver Comparison: Norris vs Verstappen")
        st.markdown("Direct contrast of race paces and degradation slope angles.")
        
        selected_stint_comp = st.sidebar.multiselect(
            "Select Stint (Comparison)", 
            options=sorted(df['Stint'].unique()), 
            default=df['Stint'].unique(),
            key="stints_comparison"
        )
        
        df_comp_filtered = df[df['Stint'].isin(selected_stint_comp)]
        
        # =========================================================
        # PEGA ESTE NUEVO BLOQUE DE ESTADÍSTICAS JUSTO AQUÍ:
        # =========================================================
        if not df_comp_filtered.empty:
            st.markdown("### 🏎️ Tire Efficiency Statistics")
            
            # Separar datos por piloto para el análisis
            lando_data = df_comp_filtered[df_comp_filtered['Driver'] == 'Lando Norris']
            max_data = df_comp_filtered[df_comp_filtered['Driver'] == 'Max Verstappen']
            
            import numpy as np
            stats = {}
            
            for name, data in [("Lando Norris", lando_data), ("Max Verstappen", max_data)]:
                if len(data) > 1:
                    avg_pace = data['LapTimeSeconds'].mean()
                    # Regresión lineal para calcular la pendiente de degradación (m)
                    slope, _ = np.polyfit(data['TyreLife'], data['LapTimeSeconds'], 1)
                    stats[name] = {"avg_pace": avg_pace, "degradation": slope}
            
            # Si ambos pilotos tienen suficientes datos, calculamos los ganadores
            if "Lando Norris" in stats and "Max Verstappen" in stats:
                col_stat1, col_stat2 = st.columns(2)
                
                # 1. Ritmo Base Promedio (Menor tiempo promedio = Más rápido)
                best_pace_driver = min(stats, key=lambda k: stats[k]["avg_pace"])
                pace_diff = abs(stats["Lando Norris"]["avg_pace"] - stats["Max Verstappen"]["avg_pace"])
                
                with col_stat1:
                    st.metric(
                        label="⚡ Best Overall Pace", 
                        value=best_pace_driver, 
                        delta=f"-{pace_diff:.3f}s / lap"
                    )
                
                # 2. Gestión de Neumáticos (Menor pendiente = El neumático se degrada más lento)
                best_deg_driver = min(stats, key=lambda k: stats[k]["degradation"])
                
                with col_stat2:
                    st.metric(
                        label="🔄 Better Tire Management", 
                        value=best_deg_driver,
                        delta=f"{stats[best_deg_driver]['degradation']:.3f}s deg/lap",
                        delta_color="inverse",
                        help="The driver with the lowest slope added less overhead time per lap as the tire aged."
                    )
            
            st.markdown("---")
            st.subheader("📊 Trend Analysis: Pace Evolution (Clean View)")
            
            # Gráfico de Seaborn (reemplazando el px.scatter anterior)
            plt.style.use("dark_background")
            fig, ax = plt.subplots(figsize=(10, 4))
            colors = {"Lando Norris": "#FF8000", "Max Verstappen": "#3671C6"}
            
            sns.lineplot(
                data=df_comp_filtered,
                x="TyreLife",
                y="LapTimeSeconds",
                hue="Driver",
                palette=colors,
                ax=ax,
                linewidth=2.5,
                errorbar=None
            )
            
            ax.set_xlabel("Tire Age (Laps)", fontsize=10)
            ax.set_ylabel("Lap Time (Seconds)", fontsize=10)
            ax.grid(True, linestyle="--", alpha=0.1)
            ax.legend(title="Driver", loc="upper left")
            plt.tight_layout()
            
            st.pyplot(fig)
            
            # Secciónde datos crudos al final
            with st.expander("Show Comparison Raw Data"):
                st.dataframe(df_comp_filtered, use_container_width=True)
        else:
            st.error("⚠️ Please select at least one Stint to render the comparison data.")

except FileNotFoundError:
    st.error("❌ No se encontró el archivo de datos. Por favor, ejecuta primero tu script de extracción para generar 'data/f1_barcelona_comparison.csv'.")
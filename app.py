import os
import sys
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Add scripts directory to module path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))
import f1_data_engine as f1e
import f1_predictive_model as f1p

# --- STREAMLIT PAGE CONFIGURATION ---
st.set_page_config(
    page_title="F1 Race Intelligence - Tire & Predictive Analytics",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for F1 Dark Mode Aesthetics
st.markdown("""
    <style>
    .main {
        background-color: #0E1117;
    }
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .f1-card {
        background-color: #161B22;
        border-left: 4px solid #E10600;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to format seconds into F1 Lap Time format (MM:SS.ms)
def format_lap_time(seconds):
    if pd.isna(seconds) or seconds <= 0:
        return "N/A"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:06.3f}"

# Cached session loader
@st.cache_data(show_spinner=False)
def get_cached_laps(year, event_name):
    return f1e.load_session_laps(year, event_name, 'R')

# --- HEADER SECTION ---
st.title("🏎️ F1 Race Intelligence Platform")
st.caption("Real-Telemetry Tire Thermal Analytics & Probabilistic Race Predictor | FIA Data Engine")
st.markdown("---")

# --- SIDEBAR CONTROLS ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg", width=120)
st.sidebar.title("Telemetry Controls")

# Mode Selection
view_mode = st.sidebar.radio(
    "Select View Mode",
    options=[
        "Single Driver Analysis",
        "Head-to-Head Comparison",
        "Pitstop Window Estimator",
        "🔮 Win Probability (Singapore 2026)"
    ]
)

st.sidebar.markdown("---")

# Conditional Data Load Controls (only when telemetric modes are selected)
if view_mode != "🔮 Win Probability (Singapore 2026)":
    st.sidebar.subheader("🏁 Race Data Source")

    data_source = st.sidebar.radio(
        "Data Load Mode",
        options=["Live FIA API (Dynamic GP)", "Local Barcelona Dataset"],
        help="Live FIA API fetches dynamic Grand Prix telemetry via FastF1. Local Dataset is pre-processed and loads instantly."
    )

    if data_source == "Local Barcelona Dataset":
        base_dir = os.path.dirname(os.path.abspath(__file__))
        local_csv = os.path.join(base_dir, 'data', 'f1_barcelona_comparison.csv')
        if os.path.exists(local_csv):
            df = pd.read_csv(local_csv)
            selected_event = "Spanish Grand Prix (Barcelona 2024)"
        else:
            st.sidebar.error("Local dataset missing. Switch to Live FIA API.")
            df = pd.DataFrame()
    else:
        col_y, col_gp = st.sidebar.columns(2)
        with col_y:
            selected_year = st.selectbox("Year", options=f1e.get_available_years(), index=0)
        
        events = f1e.get_events_for_year(selected_year)
        default_idx = events.index("Spanish Grand Prix") if "Spanish Grand Prix" in events else 0
        
        with col_gp:
            selected_event = st.selectbox("Grand Prix", options=events, index=default_idx)
            
        with st.sidebar.status(f"Loading {selected_year} {selected_event}...", expanded=False):
            df = get_cached_laps(selected_year, selected_event)
            st.write("Telemetry cleaned & indexed.")

    if df.empty:
        st.warning("⚠️ No telemetry data available for the selected race session. Please choose another race or load the local dataset.")
        st.stop()

    df['Compound'] = df['Compound'].str.upper()
    available_drivers = sorted(df['Driver'].unique())

compound_color_map = {
    'SOFT': '#FF3333',
    'MEDIUM': '#FFF200',
    'HARD': '#FFFFFF',
    'INTERMEDIATE': '#39B54A',
    'WET': '#00AEEF',
    'UNKNOWN': '#888888'
}

# ==============================================================================
# MODE 1: SINGLE DRIVER ANALYSIS
# ==============================================================================
if view_mode == "Single Driver Analysis":
    st.subheader("🏎️ Single Driver Telemetry & Tire Wear Curve")
    
    col_d, col_s = st.columns([1, 2])
    with col_d:
        selected_driver = st.selectbox("Select Driver", options=available_drivers, index=0)
    
    df_driver = df[df['Driver'] == selected_driver]
    
    with col_s:
        available_stints = sorted(df_driver['Stint'].unique())
        selected_stints = st.multiselect("Select Stint(s)", options=available_stints, default=available_stints)
        
    df_filtered = df_driver[df_driver['Stint'].isin(selected_stints)]
    
    if not df_filtered.empty:
        fastest_lap = df_filtered['LapTimeSeconds'].min()
        avg_pace = df_filtered['LapTimeSeconds'].mean()
        max_age = int(df_filtered['TyreLife'].max())
        compounds_used = ", ".join(df_filtered['Compound'].unique())
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🏎️ Primary Compound", compounds_used)
        m2.metric("⏱️ Fastest Lap Pace", format_lap_time(fastest_lap))
        m3.metric("📈 Stint Average Pace", format_lap_time(avg_pace))
        m4.metric("🔄 Maximum Tire Life", f"{max_age} Laps")
        
        st.markdown("---")
        
        st.subheader("📊 Degradation Curve (Lap Time vs Tire Age)")
        
        fig = px.scatter(
            df_filtered,
            x="TyreLife",
            y="LapTimeSeconds",
            color="Compound",
            color_discrete_map=compound_color_map,
            hover_data=["LapNumber", "Stint"],
            trendline="ols",
            title=f"{selected_driver} - Lap Time Evolution per Compound",
            labels={"TyreLife": "Tire Age (Laps)", "LapTimeSeconds": "Lap Time (Seconds)"}
        )
        fig.update_layout(template="plotly_dark", height=480)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("🔬 Stint Wear Rate Breakdown")
        stint_analysis = f1e.calculate_driver_degradation(df_filtered)
        if stint_analysis:
            df_stints = pd.DataFrame(stint_analysis)
            df_stints['SlopeSecPerLap'] = df_stints['SlopeSecPerLap'].apply(lambda x: f"{x:+.3f} s/lap")
            df_stints['AvgPaceSec'] = df_stints['AvgPaceSec'].apply(format_lap_time)
            df_stints['BasePaceSec'] = df_stints['BasePaceSec'].apply(format_lap_time)
            df_stints['R2Score'] = df_stints['R2Score'].apply(lambda x: f"{x:.2%}")
            
            st.dataframe(
                df_stints.rename(columns={
                    'Stint': 'Stint #',
                    'LapsCount': 'Total Laps',
                    'SlopeSecPerLap': 'Degradation Rate',
                    'BasePaceSec': 'Base Pace (Lap 0)',
                    'AvgPaceSec': 'Mean Stint Pace',
                    'R2Score': 'Model Fit (R²)'
                }),
                use_container_width=True
            )

# ==============================================================================
# MODE 2: HEAD-TO-HEAD DRIVER COMPARISON
# ==============================================================================
elif view_mode == "Head-to-Head Comparison":
    st.subheader("⚔️ Driver Head-to-Head Pace & Management Comparison")
    
    col1, col2 = st.columns(2)
    default_d1 = available_drivers[0]
    default_d2 = available_drivers[1] if len(available_drivers) > 1 else available_drivers[0]
    
    with col1:
        driver1 = st.selectbox("Driver 1", options=available_drivers, index=available_drivers.index(default_d1))
    with col2:
        driver2 = st.selectbox("Driver 2", options=available_drivers, index=available_drivers.index(default_d2))
        
    df_comp = df[df['Driver'].isin([driver1, driver2])]
    
    if not df_comp.empty:
        d1_data = df_comp[df_comp['Driver'] == driver1]
        d2_data = df_comp[df_comp['Driver'] == driver2]
        
        stats1 = f1e.calculate_driver_degradation(d1_data)
        stats2 = f1e.calculate_driver_degradation(d2_data)
        
        avg_pace1 = d1_data['LapTimeSeconds'].mean() if not d1_data.empty else 0
        avg_pace2 = d2_data['LapTimeSeconds'].mean() if not d2_data.empty else 0
        
        deg1 = stats1[0]['SlopeSecPerLap'] if stats1 else 0
        deg2 = stats2[0]['SlopeSecPerLap'] if stats2 else 0
        
        kpi1, kpi2, kpi3 = st.columns(3)
        
        with kpi1:
            faster_driver = driver1 if avg_pace1 < avg_pace2 else driver2
            pace_diff = abs(avg_pace1 - avg_pace2)
            st.metric("⚡ Faster Overall Pace", faster_driver, delta=f"-{pace_diff:.3f} s/lap")
            
        with kpi2:
            better_deg_driver = driver1 if deg1 < deg2 else driver2
            st.metric("🔄 Better Tire Protection", better_deg_driver, delta=f"{min(deg1, deg2):+.3f} s/lap wear", delta_color="inverse")
            
        with kpi3:
            st.metric("⏱️ Pace Delta", f"{abs(avg_pace1 - avg_pace2):.3f}s", help="Average gap per lap across analyzed stints")
            
        st.markdown("---")
        
        fig_comp = px.line(
            df_comp,
            x="TyreLife",
            y="LapTimeSeconds",
            color="Driver",
            hover_data=["LapNumber", "Compound", "Stint"],
            title=f"Race Pace Evolution: {driver1} vs {driver2}",
            labels={"TyreLife": "Tire Age (Laps)", "LapTimeSeconds": "Lap Time (s)"},
            color_discrete_sequence=["#FF8000", "#3671C6"]
        )
        fig_comp.update_layout(template="plotly_dark", height=480)
        st.plotly_chart(fig_comp, use_container_width=True)

# ==============================================================================
# MODE 3: PITSTOP WINDOW ESTIMATOR
# ==============================================================================
elif view_mode == "Pitstop Window Estimator":
    st.subheader("⏱️ Strategic Pitstop Window & Crossover Estimator")
    st.markdown("Calculates the optimal pitstop window where cumulative thermal grip degradation equals pit loss overhead.")
    
    col_p1, col_p2 = st.columns([1, 2])
    
    with col_p1:
        target_driver = st.selectbox("Select Target Driver", options=available_drivers)
        pit_loss = st.slider("Pit Stop Time Loss Penalty (Seconds)", min_value=15.0, max_value=32.0, value=22.0, step=0.5)
        
    df_target = df[df['Driver'] == target_driver]
    strategy = f1e.estimate_pitstop_window(df_target, pit_loss_seconds=pit_loss)
    
    if strategy:
        with col_p2:
            s1, s2, s3 = st.columns(3)
            s1.metric("📦 Primary Compound", strategy['PrimaryCompound'])
            s2.metric("📉 Degradation Slope", f"{strategy['DegradationSlope']:+.3f} s/lap")
            s3.metric("🎯 Optimal Pit Window", f"Laps {strategy['RecommendedWindowStart']} - {strategy['RecommendedWindowEnd']}")
            
        st.markdown("---")
        
        fig_strat = go.Figure()
        
        fig_strat.add_trace(go.Scatter(
            x=strategy['SimLaps'],
            y=strategy['SimPaceCurrent'],
            mode='lines+markers',
            name=f"{strategy['PrimaryCompound']} Degradation Projection",
            line=dict(color='#FF3333', width=3)
        ))
        
        fig_strat.add_vrect(
            x0=strategy['RecommendedWindowStart'],
            x1=strategy['RecommendedWindowEnd'],
            fillcolor="rgba(0, 255, 128, 0.2)",
            opacity=0.5,
            layer="below",
            line_width=0,
            annotation_text="OPTIMAL PIT WINDOW",
            annotation_position="top left"
        )
        
        fig_strat.update_layout(
            title=f"Projected Stint Lap Times & Pit Window Overlay ({target_driver})",
            xaxis_title="Tire Age (Laps)",
            yaxis_title="Projected Lap Time (s)",
            template="plotly_dark",
            height=480
        )
        
        st.plotly_chart(fig_strat, use_container_width=True)
        
        st.info(f"💡 **Race Strategy Insight:** For {target_driver}, on the **{strategy['PrimaryCompound']}** compound with a degradation of **{strategy['DegradationSlope']:.3f}s/lap**, pitting between **Lap {strategy['RecommendedWindowStart']} and Lap {strategy['RecommendedWindowEnd']}** prevents compounding tire wear penalties against the **{pit_loss:.1f}s** pit lane loss.")
    else:
        st.warning("Insufficient stint telemetry to calculate pitstop window model.")

# ==============================================================================
# MODE 4: WIN PROBABILITY ESTIMATOR (SINGAPORE GP 2026)
# ==============================================================================
elif view_mode == "🔮 Win Probability (Singapore 2026)":
    st.subheader("🔮 Probabilistic Win Model - Singapore Grand Prix 2026")
    st.markdown("Monte Carlo Stochastic Race Simulation (5,000 iterations) integrating 2024-2026 street circuit pace, tire wear slopes, grid position weight, and Safety Car probabilities.")
    
    st.sidebar.subheader("⚙️ Monte Carlo Parameters")
    n_sims = st.sidebar.slider("Number of Simulations", min_value=1000, max_value=10000, value=5000, step=1000)
    qualy_weight = st.sidebar.slider("Qualifying / Track Position Weight", min_value=0.20, max_value=0.80, value=0.45, step=0.05, help="Higher values increase the importance of starting position on street layout.")
    sc_prob = st.sidebar.slider("Safety Car Probability (SC/VSC)", min_value=0.50, max_value=1.00, value=0.85, step=0.05, help="Historical SC probability in Marina Bay is ~100%.")
    
    with st.spinner("Running Monte Carlo Stochastic Race Engine..."):
        df_sim = f1p.run_monte_carlo_simulation(
            n_simulations=n_sims, 
            qualy_weight=qualy_weight, 
            sc_probability=sc_prob
        )
        
    top_driver = df_sim.iloc[0]
    second_driver = df_sim.iloc[1]
    
    # Top KPI Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏆 Projected Winner", top_driver['Driver'], delta=f"{top_driver['WinProbability']:.1f}% Win Prob")
    c2.metric("🥈 Runner-Up Contender", second_driver['Driver'], delta=f"{second_driver['WinProbability']:.1f}% Win Prob")
    c3.metric("🎲 Simulations Run", f"{n_sims:,}")
    c4.metric("🚨 Safety Car Odds", f"{sc_prob*100:.0f}%")
    
    st.markdown("---")
    
    # Visualization Columns
    col_chart, col_podium = st.columns([2, 1])
    
    with col_chart:
        st.subheader("📊 Win Probability Distribution P(Win)")
        fig_prob = px.bar(
            df_sim,
            x="WinProbability",
            y="Driver",
            orientation="h",
            color="Driver",
            color_discrete_map={row['Driver']: row['Color'] for _, row in df_sim.iterrows()},
            text_auto=".1f",
            title=f"Singapore GP 2026 - Probability of Victory (%)",
            labels={"WinProbability": "Win Probability (%)", "Driver": "Driver"}
        )
        fig_prob.update_layout(template="plotly_dark", height=420, showlegend=False)
        fig_prob.update_traces(texttemplate='%{text}%', textposition='outside')
        st.plotly_chart(fig_prob, use_container_width=True)
        
    with col_podium:
        st.subheader("🥉 Podium Finish Odds P(Podium)")
        fig_pod = px.bar(
            df_sim,
            x="PodiumProbability",
            y="Driver",
            orientation="h",
            color_discrete_sequence=["#FFD700"],
            text_auto=".1f",
            title="Podium Chance (%)",
            labels={"PodiumProbability": "Podium Prob (%)", "Driver": "Driver"}
        )
        fig_pod.update_layout(template="plotly_dark", height=420, showlegend=False)
        fig_pod.update_traces(texttemplate='%{text}%', textposition='outside')
        st.plotly_chart(fig_pod, use_container_width=True)
        
    # Detailed Probability Table
    st.subheader("📋 Monte Carlo Simulation Summary Table")
    st.dataframe(
        df_sim[['Driver', 'Team', 'WinProbability', 'PodiumProbability', 'AvgFinishPosition']].rename(columns={
            'WinProbability': 'Win Chance (%)',
            'PodiumProbability': 'Podium Chance (%)',
            'AvgFinishPosition': 'Expected Finish Pos'
        }).style.format({
            'Win Chance (%)': '{:.1f}%',
            'Podium Chance (%)': '{:.1f}%',
            'Expected Finish Pos': 'P{:.1f}'
        }),
        use_container_width=True
    )
    
    st.caption("ℹ️ **Model Methodology:** Derived from multi-season street circuit telemetry (2024-2026), incorporating stochastic tire thermal wear equations, pit stop window variances, and Safety Car disruption distributions.")

# Raw Data Expander (if applicable)
if view_mode != "🔮 Win Probability (Singapore 2026)":
    with st.expander("📄 View Filtered Raw Telemetry Dataset"):
        st.dataframe(df, use_container_width=True)
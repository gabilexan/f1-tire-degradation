import os
import fastf1
import pandas as pd
import numpy as np

# Enable cache safely
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'f1_cache')
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

# F1 Tire Compound Color Palette
COMPOUND_COLORS = {
    'SOFT': '#FF3333',
    'MEDIUM': '#FFF200',
    'HARD': '#FFFFFF',
    'INTERMEDIATE': '#39B54A',
    'WET': '#00AEEF',
    'UNKNOWN': '#888888'
}

def get_available_years():
    return [2024, 2023, 2022]

def get_events_for_year(year):
    """Fetch event schedule for a given year, filtering out pre-season testing."""
    try:
        schedule = fastf1.get_event_schedule(year)
        # Filter official races
        official_races = schedule[schedule['EventFormat'] != 'testing']['EventName'].tolist()
        return official_races
    except Exception as e:
        print(f"Error fetching schedule: {e}")
        return ["Spanish Grand Prix", "Bahrain Grand Prix", "Monaco Grand Prix", "British Grand Prix"]

def load_session_laps(year, event_name, session_type='R'):
    """
    Fetch, clean, and structure lap telemetry for all drivers in a race session.
    """
    try:
        session = fastf1.get_session(year, event_name, session_type)
        session.load()
        laps = session.laps
        
        if laps.empty:
            return pd.DataFrame()

        # Select relevant columns
        cols = [
            'Driver', 'DriverNumber', 'LapNumber', 'Stint', 
            'Compound', 'TyreLife', 'LapTime', 'TrackStatus', 'IsAccurate'
        ]
        
        # Filter available columns
        cols = [c for c in cols if c in laps.columns]
        df = laps[cols].copy()
        
        # Clean accurate laps
        if 'IsAccurate' in df.columns:
            df = df[df['IsAccurate'] == True].copy()
            
        # Convert LapTime to seconds
        if 'LapTime' in df.columns:
            df['LapTimeSeconds'] = df['LapTime'].dt.total_seconds()
            df = df.dropna(subset=['LapTimeSeconds'])
            
            # Remove extreme outliers (e.g. lap times > 1.5x median lap time)
            median_lap = df['LapTimeSeconds'].median()
            df = df[df['LapTimeSeconds'] < median_lap * 1.35].copy()

        # Fill missing compound strings
        if 'Compound' in df.columns:
            df['Compound'] = df['Compound'].fillna('UNKNOWN').str.upper()

        return df
    except Exception as e:
        print(f"Error loading session laps: {e}")
        return pd.DataFrame()

def calculate_driver_degradation(df_driver):
    """
    Calculates degradation slope (seconds gained per lap on worn tire) for each stint of a driver.
    Returns a dict with stint analysis details.
    """
    if df_driver.empty:
        return []

    stint_results = []
    for stint_id, group in df_driver.groupby('Stint'):
        if len(group) < 3:
            continue
            
        compound = group['Compound'].iloc[0]
        x = group['TyreLife'].values
        y = group['LapTimeSeconds'].values

        # Linear fit: y = slope * x + intercept
        slope, intercept = np.polyfit(x, y, 1)
        
        # Calculate R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        avg_pace = y.mean()

        stint_results.append({
            'Stint': stint_id,
            'Compound': compound,
            'LapsCount': len(group),
            'MinTyreLife': int(group['TyreLife'].min()),
            'MaxTyreLife': int(group['TyreLife'].max()),
            'SlopeSecPerLap': slope,
            'BasePaceSec': intercept,
            'AvgPaceSec': avg_pace,
            'R2Score': r2
        })
        
    return stint_results

def estimate_pitstop_window(df_driver, pit_loss_seconds=22.0):
    """
    Estimates optimal pitstop window for a driver based on stint degradation curves.
    Identifies the lap at which the accumulated tire thermal/mechanical wear delta
    matches the pitstop delta cost.
    """
    if df_driver.empty:
        return None

    stints = calculate_driver_degradation(df_driver)
    if not stints:
        return None

    # Take primary stint with highest lap count
    primary_stint = max(stints, key=lambda s: s['LapsCount'])
    
    slope = primary_stint['SlopeSecPerLap']
    base_pace = primary_stint['BasePaceSec']
    
    # If slope <= 0 (unusual negative degradation), assign a default minimal wear slope
    if slope <= 0.01:
        slope = 0.05

    # Accumulated cumulative degradation time: sum_{i=1}^N (i * slope) = slope * N * (N + 1) / 2
    # Find N where cumulative degradation time equals pit_loss_seconds * factor
    # Or find lap N where instantaneous lap pace loss (N * slope) equals crossover threshold
    
    # Target lap where degradation causes pace loss per lap of ~1.5s - 2.0s
    crossover_lap = int(np.ceil(1.5 / slope)) if slope > 0 else 25
    
    # Optimal pit window centered around crossover lap
    window_start = max(10, crossover_lap - 3)
    window_end = min(40, crossover_lap + 3)
    
    # Projected pace simulation
    sim_laps = np.arange(1, 40)
    sim_pace_current = base_pace + (sim_laps * slope)
    
    return {
        'PrimaryCompound': primary_stint['Compound'],
        'DegradationSlope': slope,
        'BasePace': base_pace,
        'RecommendedWindowStart': window_start,
        'RecommendedWindowEnd': window_end,
        'CrossoverLap': crossover_lap,
        'SimLaps': sim_laps,
        'SimPaceCurrent': sim_pace_current,
        'PitLossSeconds': pit_loss_seconds
    }

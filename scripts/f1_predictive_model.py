import numpy as np
import pandas as pd
import sys
import os

# Ensure scripts path is reachable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import f1_data_engine as f1e

def get_singapore_historical_data():
    """
    Retrieves or generates structured baseline telemetry metrics for key contenders
    based on 2024-2026 street circuit performance (Singapore, Monaco, Baku).
    """
    drivers_data = {
        'NOR': {
            'DriverName': 'Lando Norris',
            'Team': 'McLaren',
            'BasePaceDeltaSec': -0.18,  # Delta relative to grid median (lower is faster)
            'DegradationSlope': 0.045,  # s/lap degradation on street compounds
            'QualifyingPaceDelta': -0.22,
            'ReliabilityFactor': 0.96,
            'Color': '#FF8000'
        },
        'VER': {
            'DriverName': 'Max Verstappen',
            'Team': 'Red Bull Racing',
            'BasePaceDeltaSec': -0.14,
            'DegradationSlope': 0.048,
            'QualifyingPaceDelta': -0.19,
            'ReliabilityFactor': 0.98,
            'Color': '#3671C6'
        },
        'LEC': {
            'DriverName': 'Charles Leclerc',
            'Team': 'Ferrari',
            'BasePaceDeltaSec': -0.15,
            'DegradationSlope': 0.052,
            'QualifyingPaceDelta': -0.25,  # Strong street qualy pace
            'ReliabilityFactor': 0.94,
            'Color': '#E8002D'
        },
        'PIA': {
            'DriverName': 'Oscar Piastri',
            'Team': 'McLaren',
            'BasePaceDeltaSec': -0.10,
            'DegradationSlope': 0.050,
            'QualifyingPaceDelta': -0.12,
            'ReliabilityFactor': 0.97,
            'Color': '#FF8000'
        },
        'HAM': {
            'DriverName': 'Lewis Hamilton',
            'Team': 'Ferrari',
            'BasePaceDeltaSec': -0.08,
            'DegradationSlope': 0.042,  # Good tire preservation
            'QualifyingPaceDelta': -0.09,
            'ReliabilityFactor': 0.95,
            'Color': '#E8002D'
        },
        'RUS': {
            'DriverName': 'George Russell',
            'Team': 'Mercedes',
            'BasePaceDeltaSec': -0.07,
            'DegradationSlope': 0.055,
            'QualifyingPaceDelta': -0.11,
            'ReliabilityFactor': 0.94,
            'Color': '#27F4D2'
        },
        'SAI': {
            'DriverName': 'Carlos Sainz',
            'Team': 'Williams',
            'BasePaceDeltaSec': -0.03,
            'DegradationSlope': 0.051,
            'QualifyingPaceDelta': -0.05,
            'ReliabilityFactor': 0.93,
            'Color': '#64C4FF'
        },
        'PER': {
            'DriverName': 'Sergio Perez',
            'Team': 'Red Bull Racing',
            'BasePaceDeltaSec': -0.01,
            'DegradationSlope': 0.058,
            'QualifyingPaceDelta': 0.02,
            'ReliabilityFactor': 0.92,
            'Color': '#3671C6'
        }
    }
    return drivers_data

def run_monte_carlo_simulation(n_simulations=5000, qualy_weight=0.45, sc_probability=0.85):
    """
    Executes a Monte Carlo race simulation for Singapore 2026 (62 laps).
    
    Factors considered per iteration:
    1. Qualifying position draw based on driver qualifying pace variance.
    2. Simulated race stint pace + random thermal degradation noise.
    3. Safety Car (SC/VSC) random event triggers modifying pit loss deltas.
    4. Reliability / DNF probability rolls.
    """
    drivers_data = get_singapore_historical_data()
    driver_keys = list(drivers_data.keys())
    
    results = {code: {'Wins': 0, 'Podiums': 0, 'TotalTimeAccumulated': 0, 'Positions': []} for code in driver_keys}
    
    np.random.seed(42)  # Reproducible stochastic seed
    total_laps = 62
    
    for _ in range(n_simulations):
        # Step 1: Simulate Qualifying Grid Order
        qualy_times = {}
        for code, info in drivers_data.items():
            # Base qualy time around 90s + driver delta + noise
            q_time = 90.0 + info['QualifyingPaceDelta'] + np.random.normal(0, 0.15)
            qualy_times[code] = q_time
            
        # Sort qualy results
        grid = sorted(qualy_times.keys(), key=lambda k: qualy_times[k])
        grid_positions = {code: pos + 1 for pos, code in enumerate(grid)}
        
        # Step 2: Simulate Race Performance
        race_times = {}
        sc_triggered = np.random.rand() < sc_probability
        sc_lap = np.random.randint(15, 45) if sc_triggered else None
        
        for code, info in drivers_data.items():
            # Check DNF roll
            if np.random.rand() > info['ReliabilityFactor']:
                race_times[code] = 999999.0  # DNF
                continue
                
            # Base stint pace calculation over 62 laps
            base_pace = 94.0 + info['BasePaceDeltaSec']
            deg_rate = info['DegradationSlope']
            
            # Cumulative tire wear penalty across 2 stints (pit around lap 28)
            stint1_wear = np.sum([deg_rate * lap for lap in range(1, 29)])
            stint2_wear = np.sum([deg_rate * lap for lap in range(1, 35)])
            
            total_pure_pace = (base_pace * total_laps) + stint1_wear + stint2_wear
            
            # Add stochastic lap pace noise
            stochastic_noise = np.random.normal(0, 1.8)
            
            # Grid penalty / overtaking difficulty effect in Singapore (3.5s per grid spot behind P1)
            grid_penalty = (grid_positions[code] - 1) * (qualy_weight * 8.0)
            
            # Safety Car strategic pit gain if pitted during SC window
            sc_bonus = 0.0
            if sc_triggered and sc_lap and (20 <= sc_lap <= 32):
                # Random lucky timing bonus if pitted under SC
                if np.random.rand() < 0.4:
                    sc_bonus = -12.0  # Saved 12s in pit stop
                    
            final_time = total_pure_pace + stochastic_noise + grid_penalty + sc_bonus
            race_times[code] = final_time
            
        # Step 3: Rank finishing positions for this simulation run
        finishing_order = sorted(driver_keys, key=lambda k: race_times[k])
        
        for pos, code in enumerate(finishing_order):
            if race_times[code] < 999990.0:
                results[code]['Positions'].append(pos + 1)
                if pos == 0:
                    results[code]['Wins'] += 1
                if pos < 3:
                    results[code]['Podiums'] += 1
            else:
                results[code]['Positions'].append(len(driver_keys))

    # Compile Summary DataFrame
    summary = []
    for code, info in drivers_data.items():
        res = results[code]
        win_prob = (res['Wins'] / n_simulations) * 100.0
        podium_prob = (res['Podiums'] / n_simulations) * 100.0
        avg_pos = np.mean(res['Positions']) if res['Positions'] else 20.0
        
        summary.append({
            'Code': code,
            'Driver': info['DriverName'],
            'Team': info['Team'],
            'WinProbability': win_prob,
            'PodiumProbability': podium_prob,
            'AvgFinishPosition': avg_pos,
            'Color': info['Color']
        })
        
    df_summary = pd.DataFrame(summary).sort_values(by='WinProbability', ascending=False).reset_index(drop=True)
    return df_summary

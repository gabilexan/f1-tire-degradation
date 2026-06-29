import fastf1
import pandas as pd
import os

# CONFIGURACIÓN DE CACHÉ
# 1. Crear físicamente la carpeta primero si no existe
if not os.path.exists('f1_cache'):
    os.makedirs('f1_cache')

# 2. Ahora sí, habilitar el caché de FastF1 de manera segura
fastf1.Cache.enable_cache('f1_cache')

# 2. Cargar la sesión: Año, Circuito, y Tipo de sesión ('R' para Carrera)
print("Descargando datos del GP...")
session = fastf1.get_session(2024, 'Barcelona', 'R')
session.load()

# 3. Obtener todas las vueltas de la carrera
all_laps = session.laps

# --- NUEVA LÓGICA DE DETECCIÓN MULTI-PILOTO ---
drivers = ['NOR', 'VER']
combined_clean_laps = []

print("Procesando telemetría de pilotos...")
for driver in drivers:
    # 4. Filtrar las vueltas del piloto en la iteración actual
    driver_laps = all_laps.pick_driver(driver)

    # 5. Limpieza básica de datos: 
    # Seleccionamos solo las columnas útiles para estudiar neumáticos
    columns_of_interest = [
        'LapNumber', 'Stint', 'Compound', 'TyreLife', 
        'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time', 
        'TrackStatus', 'IsAccurate'
    ]

    df_laps = driver_laps[columns_of_interest].copy()

    # 6. Filtrar "vueltas limpias" 
    # (IsAccurate == True elimina vueltas con Safety Car o entradas/salidas de boxes)
    df_clean = df_laps[df_laps['IsAccurate'] == True].copy()

    # Convertir el tiempo de vuelta (LapTime) a segundos para poder graficarlo/modelarlo
    df_clean['LapTimeSeconds'] = df_clean['LapTime'].dt.total_seconds()
    
    # Agregar la columna identificadora para que Streamlit separe los datos
    df_clean['Driver'] = 'Lando Norris' if driver == 'NOR' else 'Max Verstappen'
    
    # Remover la columna LapTime original (timedelta) para evitar problemas de serialización en el CSV
    df_clean = df_clean.drop(columns=['LapTime'])
    
    # Guardar en nuestra lista de consolidación
    combined_clean_laps.append(df_clean)

# Consolidar ambos dataframes en uno solo
df_final_comparison = pd.concat(combined_clean_laps, ignore_index=True)

# Mostrar las primeras vueltas en consola como control
print("\n--- Vista previa del Dataset Combinado (Primeras 5 filas) ---")
print(df_final_comparison[['Driver', 'LapNumber', 'Stint', 'Compound', 'TyreLife', 'LapTimeSeconds']].head())

## --- CÓDIGO FINAL DE GUARDADO EN GET_F1_DATA.PY ---

# Obtener la ruta absoluta del directorio del script actual ('scripts/')
script_dir = os.path.dirname(os.path.abspath(__file__))

# Subir un nivel para llegar a la raíz del proyecto y apuntar a 'data/'
project_root = os.path.abspath(os.path.join(script_dir, '..'))
output_dir = os.path.join(project_root, 'data')
output_path = os.path.join(output_dir, 'f1_barcelona_comparison.csv')

# Asegurar la creación del directorio
os.makedirs(output_dir, exist_ok=True)

# Guardar el archivo definitivo
df_final_comparison.to_csv(output_path, index=False)
print(f"\n¡Datos de comparación guardados con éxito en '{output_path}'!")
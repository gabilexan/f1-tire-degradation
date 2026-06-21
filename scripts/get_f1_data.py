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

# 4. Filtrar las vueltas de un piloto específico (ej. Lando Norris 'NOR')
driver_laps = all_laps.pick_driver('NOR')

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

# Mostrar las primeras 10 vueltas en consola
print("\n--- Primeras 10 vueltas limpias de Lando Norris ---")
print(df_clean[['LapNumber', 'Stint', 'Compound', 'TyreLife', 'LapTimeSeconds']].head(10))

# Guardar a CSV para no tener que descargar todo la próxima vez
df_clean.to_csv('norris_laps_barcelona.csv', index=False)
print("\n¡Datos guardados con éxito en 'norris_laps_barcelona.csv'!")
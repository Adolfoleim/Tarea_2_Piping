import pandas as pd
from pathlib import Path
from CoolProp.CoolProp import PropsSI
import numpy as np
import matplotlib.pyplot as plt

# Parámetros
v_max = 2.8 # m/s








# ==================================================================================================
#                           Comienzo manipulación de datos
# ==================================================================================================

# ----------------- Obtiene la ruta exacta de la carpeta donde está este script (.py)
directorio_script = Path(__file__).parent

# ----------------- Une esa ruta con el nombre de tu archivo CSV
ruta = directorio_script / 'coordenadas_sistema.xlsx'
#ruta = directorio_script / 'coordenadas_sistema_procesados.csv'

# ----------------- Lee el archivo usando la ruta absoluta que acabamos de construir
# ----------------- Para excel   ---->      df = pd.read_excel(ruta, decimal=',')
# ----------------- Para csv   ---->      df = pd.read_csv(ruta, encoding='latin-1', sep=';', decimal=',')
df = pd.read_excel(ruta, decimal=',')
# df = pd.read_csv(ruta, encoding='latin-1', sep=';', decimal=',')


# ----------------------------- Previsualización de los datos --------------------------------------
print(df.head())

# -------------------------- Operaciones para todos los segmentos ----------------------------------

# ---------------------------------- Distancia vertical --------------------------------------------
df["diff_ver_cm"] = np.where(df['punto_idx'] > 1, - df["y_cm"].diff().fillna(0), 0)

# ---------------------------------- Separar segmentos ---------------------------------------------
df_AB = df[df["tramo"] == "A-B"].copy() # Tramo A-B
df_BC = df[df["tramo"] == "B-C"].copy() # Tramo B-C
df_CD = df[df["tramo"] == "C-D"].copy() # Tramo C-D
df_DE = df[df["tramo"] == "D-E"].copy() # Tramo D-E

df_DE_MA = df_DE[df_DE['escenario_marea'].isin(["Base", "Marea alta"])].copy()
df_DE_BMA = df_DE[df_DE['escenario_marea'].isin(["Base", "1.5m bajo marea alta"])].copy()
df_DE_MM = df_DE[df_DE['escenario_marea'].isin(["Base", "Marea media"])].copy()
df_DE_SMB = df_DE[df_DE['escenario_marea'].isin(["Base", "1.5m sobre marea baja"])].copy()
df_DE_MB = df_DE[df_DE['escenario_marea'].isin(["Base", "Marea baja"])].copy()


# -------------------------- Previsualizo si quedaron bien -----------------------------------------
#print(df_AB.head())
#print(df_BC.head())
#print(df_CD.head())
#print(df_DE.head())

# Operaciones por tramo


# ==================================================================================================
#                               Término manipulación de datos
# ==================================================================================================








# ==================================================================================================
#                                           Gráficos
# ==================================================================================================

# Comienzo mi gráfico
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

# Graficar los puntos unidos por líneas
ax.plot(df_AB['x_cm'], df_AB['z_cm'], df_AB['y_cm'], color='blue', marker='o', label='Fase 1')
ax.plot(df_BC['x_cm'], df_BC['z_cm'], df_BC['y_cm'], color='c', marker='o', label='Fase 2')
ax.plot(df_CD['x_cm'], df_CD['z_cm'], df_CD['y_cm'], color='r', marker='o', label='Fase 3')
ax.plot(df_DE_MB['x_cm'], df_DE_MB['z_cm'], df_DE_MB['y_cm'], color='green', marker='o', label='Fase 4')


# Etiquetas de los ejes
ax.set_xlabel('Eje X')
ax.set_ylabel('Eje Y')
ax.set_zlabel('Eje Z')
ax.set_title('Gráfico de Líneas en 3D')
ax.legend()

plt.show()


# ==================================================================================================
#                               Guardo en un archivo CSV
# ==================================================================================================


ruta_salida = directorio_script / 'coordenadas_sistema_procesados.csv'
#ruta_salida = directorio_script / 'coordenadas_sistema_procesados_2.csv'

# Guardamos el DataFrame

df.to_csv(ruta_salida, 
          sep=';',           # Separador de columnas
          decimal=',',       # Separador de decimales (estándar chileno/Excel)
          encoding='latin-1' # Para que Excel reconozca bien los caracteres
)

print(f"Archivo guardado exitosamente en: {ruta_salida}")
import pandas as pd
from pathlib import Path
from CoolProp.CoolProp import PropsSI
import numpy as np
import matplotlib.pyplot as plt
import fluids as fld
from fluids.units import *
from scipy.constants import g

# ==================================================================================================
#                               Parámetros
# ==================================================================================================

# Factor de fricción de entrada y salida
K_entrance = fld.fittings.entrance_sharp('Rennels')
K_exit = fld.fittings.exit_normal()

# Gravedad
g = g * u.m/u.s**2

# Velocidad máxima del fluido
v_max = 2.8 * u.m/u.s # m/s

# Caudal de tramos
Q_ab = 50 / 3600 * u.m **3 / u.s # m3/h a m3/s
Q_cd = 25 / 3600 * u.m **3 / u.s # m3/h a m3/s

# Densidad y viscosidad cinemática del agua de mar
rho = 1026 * u.kg / u.m**3 # kg/m3
visc = 1e-6 * u.m **2 / u.s  # m2/s
mu = (visc * rho).to("Pa*s")

# Propiedades tubería HDPE
epsilon = 1.5e-6 * u.m # m
n = 0.010 # Coeficiente de Manning

# ------------- Ecuación de Manning para Tubería Circular Parcialmente Llena -----------------------
# La ecuación de Manning describe el caudal en función de la geometría de la sección mojada
# y la pendiente de la línea de energía



# ==================================================================================================
#                               Funciones
# ==================================================================================================

def Q_man(A, R_h, S_f, n=n):
    Q = A * R_h ** 2/3 * S_f ** 1/2 / n
    return Q

    # Q [m3/s]: caudal volumétrico
    # n [m-1/3 s]: coeficiente de rugosidad de Manning del material (HDPE: n = 0.010)
    # A [m2]: área de la sección transversal
    # R_h [m]: Radio hidráulico (R_h = A/P)
    # S_f [m/m]: pendiente de la línea de energía

# Bajo hipótesis de flujo uniforme en cada tramo, la línea de energía es paralela al fondo de la 
# tubería, por lo que puede aproximarse S_f ≈ S_0, donde S_0 es la pendiente de fondo del subtramo: 
def S_f(y_a, y_b, L):
    S_0 = (y_a - y_b) / L
    return S_0

    # y_a [m]: fondo - aguas arriba
    # y_b [m]: fondo - aguas abajo
    # L [m]: Largo subtramo

# ------------- Funciones en base a la figura 2: ----------------

    # D [m]: diámetro de la tubería circular
    # h [m]: profundidad del agua medida desde el fondo
    # P [rad]: Arco de la tubería mojada
    # A [m2]: Área de la tubería mojada
    # R_h [m]: Radio hidráulico
    # V [m/s]: Velocidad media

# Propiedades tubería mojada según Figura 2
def Para_tub(D, h, Q):
    theta = 2 * np.arccos(1 - 2*h/D) # ángulo mojado en radianes
    A = D ** 2 * (theta - np.sin(theta)) / 8 # Área de la tubería mojada
    P = D*theta / 2 # Arco de la tubería mojada
    R_h = A / P # Radio hidráulico
    V = Q / A # Velocidad media
    return A, R_h, V


    

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
# -----------------  Para csv   ---->      df = pd.read_csv(ruta, encoding='latin-1', sep=';', decimal=',')
df = pd.read_excel(ruta, decimal=',')
# df = pd.read_csv(ruta, encoding='latin-1', sep=';', decimal=',')


# ----------------------------- Previsualización de los datos --------------------------------------
#print(df.head())

# -------------------------- Operaciones para todos los segmentos ----------------------------------

# ---------------------------------- Distancia vertical --------------------------------------------
df["diff_ver_cm"] = np.where(df['punto_idx'] > 1, - df["y_cm"].diff().fillna(0), 0)

# ---------------------------------- Separar segmentos ---------------------------------------------
df_AB = df[df["tramo"] == "A-B"].copy() # Tramo A-B
df_BC = df[df["tramo"] == "B-C"].copy() # Tramo B-C
df_CD = df[df["tramo"] == "C-D"].copy() # Tramo C-D
df_DE = df[df["tramo"] == "D-E"].copy() # Tramo D-E

df_DE_MA = df_DE[df_DE['escenario_marea'].isin(["Base", "Marea alta"])].copy()              # Tramo D-E con Marea Alta
df_DE_BMA = df_DE[df_DE['escenario_marea'].isin(["Base", "1.5m bajo marea alta"])].copy()   # Tramo D-E con 1.5m bajo Marea Alta
df_DE_MM = df_DE[df_DE['escenario_marea'].isin(["Base", "Marea media"])].copy()             # Tramo D-E con Marea Media
df_DE_SMB = df_DE[df_DE['escenario_marea'].isin(["Base", "1.5m sobre marea baja"])].copy()  # Tramo D-E con 1.5m sobre Marea Baja
df_DE_MB = df_DE[df_DE['escenario_marea'].isin(["Base", "Marea baja"])].copy()              # Tramo D-E con Marea Baja


# -------------------------- Previsualizo si quedaron bien -----------------------------------------
#print(df_AB.head())
#print(df_BC.head())
#print(df_CD.head())
#print(df_DE.head())

# Operaciones por tramo


# ==================================================================================================
#                               Término manipulación de datos
# ==================================================================================================

# ========================================== Tramo B-C =============================================

Q_max_BC = 340 * u.m**3/u.h  #m/h
D_BC = df_BC['diametro_m_excel'].iloc[0] * u.m # m Diametro D_BC en excel
A_BC = (np.pi * (D_BC / 2)**2).to("m**2") 
V_BC = (Q_max_BC / A_BC).to("m/s")
z_1 = (df_BC['y_cm'].iloc[0] * u.cm).to('m')
z_2 = (df_BC['y_cm'].iloc[-1] * u.cm).to('m') #Altura z_2 en excel
print(f'Velocidad: {V_BC}')
L_BC = (df_BC['dist_acum_m'].iloc[-1] *u.m) #Largo tubería L_BC en excel
print(f'Largo: {L_BC}')

Re_BC = (fld.Reynolds(D_BC, rho, V_BC, mu)).to('dimensionless')
print(f'Reynolds: {Re_BC}')

f_BC = fld.friction.friction_factor(Re_BC, eD=epsilon/D_BC, Method='Colebrook')
print(f'Factor de fricción: {f_BC}')

Delta_P = ( ((V_BC ** 2 / (2 *g)) * (f_BC * L_BC / D_BC + K_entrance + K_exit) + z_2 - z_1) * rho * g ).to('kPa')
print(f'Diferencia de presión: {Delta_P}')

# ==================================================================================================
#                                           Gráficos
# ==================================================================================================

# Comienzo mi gráfico
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

# Graficar los puntos unidos por líneas
ax.plot(df_AB['x_cm'], df_AB['y_cm'], df_AB['z_cm'], color='blue', marker='o', label='Tramo A-B')
ax.plot(df_BC['x_cm'], df_BC['y_cm'], df_BC['z_cm'], color='c', marker='o', label='Tramo B-C')
ax.plot(df_CD['x_cm'], df_CD['y_cm'], df_CD['z_cm'], color='r', marker='o', label='Tramo C-D')
ax.plot(df_DE_MB['x_cm'], df_DE_MB['y_cm'], df_DE_MB['z_cm'], color='green', marker='o', label='Tramo D-E')


# Etiquetas de los ejes
ax.set_xlabel('Eje X')
ax.set_ylabel('Eje Y')
ax.set_zlabel('Eje Z')
ax.set_title('Gráfico de Líneas en 3D')
ax.legend()

#plt.show()


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
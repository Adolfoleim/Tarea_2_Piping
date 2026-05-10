import pandas as pd
from pathlib import Path
from CoolProp.CoolProp import PropsSI
import numpy as np
import matplotlib.pyplot as plt
import fluids as fld
from fluids.units import *
from scipy.constants import g
from scipy.optimize import brentq
from scipy.signal import find_peaks

# ==================================================================================================
#                               Parámetros
# ==================================================================================================

# Factor de fricción de entrada y salida
K_entrance = fld.fittings.entrance_sharp('Rennels')
K_exit = fld.fittings.exit_normal()
K_total = K_entrance + K_exit

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
gamma = (rho * g).to("N/m**3") # Peso específico del agua de mar

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
#df["diff_ver_cm"] = np.where(df['punto_idx'] > 1, - df["y_cm"].diff().fillna(0), 0)

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

# Parámetros fijos
D_BC = df_BC['diametro_m_excel'].iloc[0] * u.m      # Diámetro
A_BC = (np.pi * (D_BC / 2)**2).to("m**2")           # Área

# Variables
z_2_BC = df_BC['y_cm'].values*u.cm              # Altura de cada punto del tramo B-C a analizar
L_BC = df_BC['dist_acum_m'].values*u.m          # Largo de la tubería en cada punto del tramo B-C
L_total_BC = df_BC['dist_acum_m'].iloc[-1]*u.m  # Largo total en el último punto del tramo B-C

# Altura inicial escogida
z_B = df_AB['y_cm'].iloc[-1] * u.cm             # Altura del Estanque - Altura término tramo A-B
z_f_BC = df_BC['y_cm'].iloc[-1] * u.cm          # Altura del último punto del tramo B-C

# ================== Determino velocidad del fluido con mi altura impuesta =========================
# Método numérico implícito utilizado Brent
# Defino primero mi función, que en este caso es el balance de energía:

def Balance_BC(v, arg):
    z1 = (arg['z1']).to('m').magnitude
    z2 = (arg['z2']).to('m').magnitude
    L  = arg['L'].magnitude
    D  = arg['D'].magnitude
    K  = arg['K']
    g  = arg['g'].magnitude
    rho= arg['rho'].magnitude
    mu = arg['mu'].magnitude
    epsilon = arg['epsilon'].magnitude
    
    Re = (fld.Reynolds(D, rho, v, mu))
    f = (fld.friction.friction_factor(Re, eD=epsilon/D, Method='Colebrook'))
    residuo = z2-z1 + (v) ** 2 / (2*g) * (f * L/D + K + 1)
    return residuo

arg = {'z1': z_B,
       'z2': z_f_BC,
       'L': L_total_BC,
       'D': D_BC,
       'K': K_total,
       'g': g,
       'rho': rho,
       'mu': mu,
       'epsilon': epsilon}


v_min = 0.1
v_max = 2.8
rango_v = [v_min, v_max]

v_real = brentq(Balance_BC, rango_v[0], rango_v[1], args=arg)

# ================== Sigo con el análisis del tramo con la velocidad encontrada ====================

# Velocidad encontrada
V_BC = v_real * u.m/u.s                             # Velocidad de flujo
Q_max_BC = (V_BC * A_BC).to('m**3/h')               # Caudal impuesto

# Parámetros dependientes de velocidad
Re_BC = (fld.Reynolds(D_BC, rho, V_BC, mu)).to('dimensionless')
f_BC = (fld.friction.friction_factor(Re_BC, eD=epsilon/D_BC, Method='Colebrook')).to('dimensionless')

# Pérdidas [metros]
df_BC['Perdidas_BC'] = ((V_BC**2/(2*g) * (f_BC*L_BC/D_BC + K_entrance)).to('m')).magnitude
df_BC.loc[df_BC.index[-1], 'Perdidas_BC'] = ((V_BC**2/(2*g) * (f_BC*L_BC[-1]/D_BC + K_total)).to('m')).magnitude
# Diferencia de Energía cinética [metros]
df_BC['E_V_BC'] = ((V_BC**2/(2*g)).to('m')).magnitude
# Presión 2 (Delta de presión) [kPa]
df_BC['P_BC'] = (((z_B - z_2_BC - V_BC**2/(2*g) * (f_BC*L_BC/D_BC + K_entrance + 1))*gamma).to('kPa')).magnitude
df_BC.loc[df_BC.index[-1], 'P_BC'] = ((z_B - z_2_BC[-1] - V_BC**2/(2*g) * (f_BC*L_BC[-1]/D_BC + K_total + 1))*gamma).to('kPa').magnitude
# Presión 2 (Delta de presión) [metros]
df_BC['P_BC_m'] = (((z_B - z_2_BC - V_BC**2/(2*g) * (f_BC*L_BC/D_BC + K_entrance + 1))).to('m')).magnitude
df_BC.loc[df_BC.index[-1], 'P_BC_m'] = (z_B - z_2_BC[-1] - V_BC**2/(2*g) * (f_BC*L_BC[-1]/D_BC + K_total + 1)).to('m').magnitude

P_BC = df_BC['P_BC'].values*u.kPa

print(f"Velocidad real: {V_BC}")
print(f'Diametro: {D_BC}')
print(f'Velocidad: {V_BC}')
print(f'Reynolds: {Re_BC}')
print(f'Factor de fricción: {f_BC}')
print(f'P_1: 0')

df_BC['Piezometrico'] = (z_2_BC + P_BC / gamma - z_f_BC).to('m').magnitude
df_BC['E_Potencial'] = (z_B-z_2_BC).to('m').magnitude



# ==================================================================================================
#                                      Máximos y Mínimos Tramo B-C
# ==================================================================================================


# ==================================================================================================
#                                           Gráfico Tramo B-C
# ==================================================================================================



fig, ax1 = plt.subplots(figsize=(8, 5))

# Eje Izquierdo (ax1) - Para la Presión
ax1.plot(df_BC['dist_acum_m'], df_BC['P_BC'], color='blue', marker='o', label='Presión [kPa]')
ax1.set_xlabel('Recorrido [m]')
ax1.set_ylabel('Presión [kPa]', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.grid(True)

# Eje Derecho (ax2) - Para la Piezométrica
ax2 = ax1.twinx()  # Crea un eje Y gemelo que comparte el eje X
ax2.plot(df_BC['dist_acum_m'], df_BC['Piezometrico'], color='c', marker='s', label='Línea Piezométrica [m]')
ax2.set_ylabel('Línea Piezométrica', color='c')
ax2.tick_params(axis='y', labelcolor='c')

ax1.set_title('Perfil de Presión y Línea Piezométrica tramo B-C')

# Para juntar las leyendas de ambos ejes
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

plt.savefig(directorio_script / 'Presión y Línea Piezométrica Tramo BC.png', dpi=300, bbox_inches='tight')
plt.show()



plt.figure(figsize=(8, 5))
plt.plot(df_BC['dist_acum_m'], df_BC['P_BC'], color='blue', marker='o', label='Presión [kPa]')
plt.title('Perfil de Presión tramo B-C')
plt.xlabel('Recorrido [m]')
plt.ylabel('Presión [kPa]')
plt.grid(True) # Cuadrícula
plt.legend()   # Mostrar leyenda

plt.savefig(directorio_script / 'Presión Tramo BC.png', dpi=300, bbox_inches='tight')
plt.show()

plt.figure(figsize=(8, 5))
plt.plot(df_BC['dist_acum_m'], df_BC['Piezometrico'], color='c', marker='s', label='Línea Piezométrica [m]')
plt.title('Línea Piezométrica tramo B-C')
plt.xlabel('Recorrido [m]')
plt.ylabel('Línea Piezométrica [m]')
plt.grid(True) # Cuadrícula
plt.legend()   # Mostrar leyenda

plt.savefig(directorio_script / 'Línea Piezométrica Tramo BC.png', dpi=300, bbox_inches='tight')
plt.show()

# ================================ Gráfico elementos Balance =======================================

fig, ax = plt.subplots(figsize=(8, 5))

# Graficar líneas
ax.plot(df_BC['dist_acum_m'], df_BC['P_BC_m'], color='blue', linestyle='--', marker='o', label='Delta Energía de flujo [m]')
ax.plot(df_BC['dist_acum_m'], (z_B-z_2_BC).to('m').magnitude, color='c', linestyle='--', marker='s', label='Delta Energía potencial [m]')
ax.plot(df_BC['dist_acum_m'], df_BC['E_V_BC'], color='black', linestyle='--', marker='*', label='Delta Energía Cinética [m]')
ax.plot(df_BC['dist_acum_m'], df_BC['Perdidas_BC'], color='red', linestyle='--', marker='v', label='Pérdidas [m]')

# Personalización
ax.set_title('Elementos del balance de energía a lo largo del tramo B-C')
ax.set_xlabel('Recorrido [m]')
ax.set_ylabel('Presión / Altura / Pérdidas [m]') # Nombre genérico si comparten la misma unidad
ax.grid(True)
ax.legend()

plt.savefig(directorio_script / 'Elementos Balance Tramo BC.png', dpi=300, bbox_inches='tight')
plt.show()


# ==================================================================================================
#                                           Gráfico 3D
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


plt.show()


# ==================================================================================================
#                               Guardo en un archivo CSV
# ==================================================================================================


ruta_salida = directorio_script / 'Tramo B-C.csv'
#ruta_salida = directorio_script / 'coordenadas_sistema_procesados_2.csv'

# Guardamos el DataFrame

df_BC.to_csv(ruta_salida, 
          sep=';',           # Separador de columnas
          decimal=',',       # Separador de decimales (estándar chileno/Excel)
          encoding='latin-1' # Para que Excel reconozca bien los caracteres
)

print(f"Archivo guardado exitosamente en: {ruta_salida}")
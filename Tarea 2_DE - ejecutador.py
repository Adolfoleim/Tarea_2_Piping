import pandas as pd
from pathlib import Path
from CoolProp.CoolProp import PropsSI
import numpy as np
import matplotlib.pyplot as plt
import fluids as fld
from fluids.units import *
from scipy.constants import g
from scipy.optimize import brentq
from matplotlib.animation import FuncAnimation

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
#                           Comienzo manipulación de datos
# ==================================================================================================

# ----------------- Obtiene la ruta exacta de la carpeta donde está este script (.py)
directorio_script = Path(__file__).parent

# ----------------- Une esa ruta con el nombre de tu archivo CSV

ruta = directorio_script / 'coordenadas_sistema.xlsx'
ruta_1 = directorio_script / 'Tramo_DE_MA.csv'
ruta_2 = directorio_script / 'Tramo_DE_BMA.csv'
ruta_3 = directorio_script / 'Tramo_DE_MB.csv'
ruta_4 = directorio_script / 'Tramo_DE_SMB.csv'
ruta_5 = directorio_script / 'Tramo_DE_MB.csv'
#ruta = directorio_script / 'coordenadas_sistema_procesados.csv'

# ----------------- Lee el archivo usando la ruta absoluta que acabamos de construir
# ----------------- Para excel   ---->      df = pd.read_excel(ruta, decimal=',')
# -----------------  Para csv   ---->      df = pd.read_csv(ruta, encoding='latin-1', sep=';', decimal=',')
df = pd.read_excel(ruta, decimal=',')
df_CD = df[df["tramo"] == "C-D"].copy() # Tramo C-D
df_DE_MA =  pd.read_csv(ruta_1, encoding='latin-1', sep=';', decimal=',')
df_DE_BMA = pd.read_csv(ruta_2, encoding='latin-1', sep=';', decimal=',')
df_DE_MM =  pd.read_csv(ruta_3, encoding='latin-1', sep=';', decimal=',')
df_DE_SMB = pd.read_csv(ruta_4, encoding='latin-1', sep=';', decimal=',')
df_DE_MB =  pd.read_csv(ruta_5, encoding='latin-1', sep=';', decimal=',')
# df = pd.read_csv(ruta, encoding='latin-1', sep=';', decimal=',')


# ========================================== Tramo B-C =============================================

# Parámetros fijos
D_DE = df_DE_MA['diametro_m_excel'].iloc[0] * u.m      # Diámetro
A_DE = (np.pi * (D_DE / 2)**2).to("m**2")           # Área

# ALTURAS POR MAREA
z_2_DE_MA   =   df_DE_MA['y_cm'].values*u.cm        # Altura de cada punto del tramo D-E con Marea Alta
z_2_DE_BMA  =   df_DE_BMA['y_cm'].values*u.cm       # Altura de cada punto del tramo D-E con 1.5m bajo Marea Alta
z_2_DE_MM   =   df_DE_MM['y_cm'].values*u.cm        # Altura de cada punto del tramo D-E con Marea Media
z_2_DE_SMB  =   df_DE_SMB['y_cm'].values*u.cm       # Altura de cada punto del tramo D-E con 1.5m sobre Marea Baja
z_2_DE_MB   =   df_DE_MB['y_cm'].values*u.cm        # Altura de cada punto del tramo D-E con Marea Baja

# LARGOS POR MAREA
L_DE_MA     =   df_DE_MA['dist_acum_m'].values*u.m  # Largo de la tubería en cada punto del tramo D-E con Marea Alta
L_DE_BMA    =   df_DE_BMA['dist_acum_m'].values*u.m # Largo de la tubería en cada punto del tramo D-E con 1.5m bajo Marea Alta
L_DE_MM     =   df_DE_MM['dist_acum_m'].values*u.m  # Largo de la tubería en cada punto del tramo D-E con Marea Media
L_DE_SMB    =   df_DE_SMB['dist_acum_m'].values*u.m # Largo de la tubería en cada punto del tramo D-E con 1.5m sobre Marea Baja
L_DE_MB     =   df_DE_MB['dist_acum_m'].values*u.m  # Largo de la tubería en cada punto del tramo D-E con Marea Baja

L_total_DE_MA   =   df_DE_MA['dist_acum_m'].iloc[-1]*u.m    # Largo total en el último punto del tramo D-E con Marea Alta
L_total_DE_BMA  =   df_DE_BMA['dist_acum_m'].iloc[-1]*u.m   # Largo total en el último punto del tramo D-E con 1.5m bajo Marea Alta
L_total_DE_MM   =   df_DE_MM['dist_acum_m'].iloc[-1]*u.m    # Largo total en el último punto del tramo D-E con Marea Media
L_total_DE_SMB  =   df_DE_SMB['dist_acum_m'].iloc[-1]*u.m   # Largo total en el último punto del tramo D-E con 1.5m sobre Marea Baja
L_total_DE_MB   =   df_DE_MB['dist_acum_m'].iloc[-1]*u.m    # Largo total en el último punto del tramo D-E con Marea Baja

# Altura inicial escogida
z_D = df_CD['y_cm'].iloc[-1] * u.cm             # Altura del Estanque - Altura término tramo A-B

z_f_DE_MA   =   df_DE_MA['y_cm'].iloc[-1]*u.cm      # Altura del último punto del tramo D-E con Marea Alta
z_f_DE_BMA  =   df_DE_BMA['y_cm'].iloc[-1]*u.cm     # Altura del último punto del tramo D-E con 1.5m bajo Marea Alta
z_f_DE_MM   =   df_DE_MM['y_cm'].iloc[-1]*u.cm      # Altura del último punto del tramo D-E con Marea Media
z_f_DE_SMB  =   df_DE_SMB['y_cm'].iloc[-1]*u.cm     # Altura del último punto del tramo D-E con 1.5m sobre Marea Baja
z_f_DE_MB   =   df_DE_MB['y_cm'].iloc[-1]*u.cm      # Altura del último punto del tramo D-E con Marea Baja

# ================== Determino velocidad del fluido con mi altura impuesta =========================
# Método numérico implícito utilizado Brent
# Defino primero mi función, que en este caso es el balance de energía, SOLO para el caso más y
# menos favorable, en este caso, en la marea baja y marea alta:

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

arg_MA = {'z1': z_D,
       'z2': z_f_DE_MA,
       'L': L_total_DE_MA,
       'D': D_DE,
       'K': K_total,
       'g': g,
       'rho': rho,
       'mu': mu,
       'epsilon': epsilon}

arg_BMA = {'z1': z_D,
       'z2': z_f_DE_BMA,
       'L': L_total_DE_BMA,
       'D': D_DE,
       'K': K_total,
       'g': g,
       'rho': rho,
       'mu': mu,
       'epsilon': epsilon}

arg_MM = {'z1': z_D,
       'z2': z_f_DE_MM,
       'L': L_total_DE_MM,
       'D': D_DE,
       'K': K_total,
       'g': g,
       'rho': rho,
       'mu': mu,
       'epsilon': epsilon}

arg_SMB = {'z1': z_D,
       'z2': z_f_DE_SMB,
       'L': L_total_DE_SMB,
       'D': D_DE,
       'K': K_total,
       'g': g,
       'rho': rho,
       'mu': mu,
       'epsilon': epsilon}

arg_MB = {'z1': z_D,
       'z2': z_f_DE_MB,
       'L': L_total_DE_MB,
       'D': D_DE,
       'K': K_total,
       'g': g,
       'rho': rho,
       'mu': mu,
       'epsilon': epsilon}


v_min = 0.1
v_max = 2.8
rango_v = [v_min, v_max]

v_real_MA = brentq(Balance_BC, rango_v[0], rango_v[1], args=arg_MA)
v_real_BMA = brentq(Balance_BC, rango_v[0], rango_v[1], args=arg_BMA)
v_real_MM = brentq(Balance_BC, rango_v[0], rango_v[1], args=arg_MM)
v_real_SMB = brentq(Balance_BC, rango_v[0], rango_v[1], args=arg_SMB)
v_real_MB = brentq(Balance_BC, rango_v[0], rango_v[1], args=arg_MB)


# Velocidad encontrada
V_DE_MA = v_real_MA* u.m/u.s                           # Velocidad de flujo
V_DE_BMA = v_real_BMA* u.m/u.s
V_DE_MM = v_real_MM* u.m/u.s
V_DE_SMB = v_real_SMB* u.m/u.s
V_DE_MB = v_real_MB* u.m/u.s

Q_max_BC = (V_DE_MA * A_DE).to('m**3/h')               # Caudal impuesto



# ==================================================================================================
#                                           Gráfico Tramo B-C
# ==================================================================================================



fig, ax1 = plt.subplots(figsize=(8, 5))

# Eje Izquierdo (ax1) - Para la Presión
ax1.plot(df_DE_MA['dist_acum_m'], df_DE_MA['P_DE_MA'], color='blue', marker='o', label='Presión [kPa]')
ax1.set_xlabel('Recorrido [m]')
ax1.set_ylabel('Presión [kPa]', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.grid(True)

# Eje Derecho (ax2) - Para la Piezométrica
ax2 = ax1.twinx()  # Crea un eje Y gemelo que comparte el eje X
ax2.plot(df_DE_MA['dist_acum_m'], df_DE_MA['Piezometrico'], color='c', marker='s', label='Línea Piezométrica [m]')
ax2.set_ylabel('Línea Piezométrica', color='c')
ax2.tick_params(axis='y', labelcolor='c')

ax1.set_title('Perfil de Presiones (Doble Escala)')

# Para juntar las leyendas de ambos ejes
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

plt.show()

# ================================ Gráfico elementos Balance =======================================

fig, ax = plt.subplots(figsize=(8, 5))

# Graficar líneas
ax.plot(df_DE_MA['dist_acum_m'], df_DE_MA['P_DE_MA_m'], color='blue', linestyle='--', marker='o', label='Diferencia de Presión [m]')
ax.plot(df_DE_MA['dist_acum_m'], (z_D-z_2_DE_MA).to('m').magnitude, color='c', linestyle='--', marker='s', label='Diferencia de altura [m]')
ax.plot(df_DE_MA['dist_acum_m'], df_DE_MA['Perdidas_DE_MA'], color='red', linestyle='--', marker='v', label='Pérdidas [m]')
ax.plot(df_DE_MA['dist_acum_m'], df_DE_MA['E_V_DE_MA'], color='black', linestyle='--', marker='*', label='E. Cinética [m]')

# Personalización
ax.set_title('Elementos del balance de energía a lo largo del recorrido')
ax.set_xlabel('Recorrido [m]')
ax.set_ylabel('Presión / Altura / Pérdidas [m]') # Nombre genérico si comparten la misma unidad
ax.grid(True)
ax.legend()

plt.show()


# ==================================================================================================
#                                           Gráfico 3D
# ==================================================================================================

# Comienzo mi gráfico
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

# Graficar los puntos unidos por líneas
#ax.plot(df_AB['x_cm'], df_AB['y_cm'], df_AB['z_cm'], color='blue', marker='o', label='Tramo A-B')
#ax.plot(df_BC['x_cm'], df_BC['y_cm'], df_BC['z_cm'], color='c', marker='o', label='Tramo B-C')
#ax.plot(df_CD['x_cm'], df_CD['y_cm'], df_CD['z_cm'], color='r', marker='o', label='Tramo C-D')
ax.plot(df_DE_MB['x_cm'], df_DE_MB['y_cm'], df_DE_MB['z_cm'], color='green', marker='o', label='Tramo D-E')



# Etiquetas de los ejes
ax.set_xlabel('Eje X')
ax.set_ylabel('Eje Y')
ax.set_zlabel('Eje Z')
ax.set_title('Gráfico de Líneas en 3D')
ax.legend()

plt.show()


# 1. Configuración inicial del gráfico
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

# Creamos una línea vacía que iremos llenando
line, = ax.plot([], [], [], color='green', marker='o', lw=2, label='Tramo D-E')

# Configurar límites de los ejes (ajusta según tus datos para que no "salte" el gráfico)
ax.set_xlim(df_DE_MB['x_cm'].min(), df_DE_MB['x_cm'].max())
ax.set_ylim(df_DE_MB['y_cm'].min(), df_DE_MB['y_cm'].max())
ax.set_zlim(df_DE_MB['z_cm'].min(), df_DE_MB['z_cm'].max())

ax.set_xlabel('Eje X')
ax.set_ylabel('Eje Y')
ax.set_zlabel('Eje Z')
ax.set_title('Progreso de Trazado: Tramo D-E')
ax.legend()

# 2. Función de actualización (qué pasa en cada frame)
def update(frame):
    # 'frame' es un número que va de 0 hasta el total de puntos
    data = df_DE_MB.iloc[:frame+1]
    line.set_data(data['x_cm'], data['y_cm'])
    line.set_3d_properties(data['z_cm'])
    return line,

# 3. Crear la animación
# frames: cantidad de puntos en el dataframe
# interval: milisegundos entre cada punto (ej. 100ms)
# repeat: si quieres que vuelva a empezar al terminar
ani = FuncAnimation(fig, update, frames=len(df_DE_MB), interval=100, blit=False, repeat=True)

plt.show()


# ==================================================================================================
#                               Guardo en un archivo CSV
# ==================================================================================================


r_1 = directorio_script / 'Tramo_DE_MA.csv'
r_2 = directorio_script / 'Tramo_DE_BMA.csv'
r_3 = directorio_script / 'Tramo_DE_MM.csv'
r_4 = directorio_script / 'Tramo_DE_SMB.csv'
r_5 = directorio_script / 'Tramo_DE_MB.csv'
#ruta_salida = directorio_script / 'coordenadas_sistema_procesados_2.csv'
rutas = [r_1, r_2, r_3, r_4, r_5]
doc = [df_DE_MA, df_DE_BMA, df_DE_MM, df_DE_MM, df_DE_SMB, df_DE_MB]
# Guardamos el DataFrame
for i in range(5):
    doc[i].to_csv(rutas[i], 
              sep=';',           # Separador de columnas
              decimal=',',       # Separador de decimales (estándar chileno/Excel)
              encoding='latin-1' # Para que Excel reconozca bien los caracteres
    )
    print(f"Archivo guardado exitosamente en: {rutas[i]}")
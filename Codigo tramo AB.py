import pandas as pd
from pathlib import Path
import numpy as np
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
from fluids.open_flow import V_Manning
from scipy.constants import g
from fluids.friction import friction_factor
from fluids.fittings import entrance_sharp, exit_normal

# Lectura de datos
directorio_script = Path(__file__).parent
ruta_excel = directorio_script / 'coordenadas_sistema.xlsx'
df = pd.read_excel(ruta_excel)
# Filtrar tramo AB
df_AB = df[df["tramo"] == "A-B"].sort_values("punto_idx").reset_index(drop=True)

# Datos enunciado
Q_AB = 50 / 3600 # [m3/s]
n = 0.010 # Manning HDPE
D = df_AB.iloc[0]["diametro_m_excel"]

# Funciones
def Q_calculado(h, S0):
    if np.any(h <= 0) or np.any(h >= D):
        return 1e6
    theta = 2 * np.arccos(1 - 2*h/D)
    A = (D**2 / 8) * (theta - np.sin(theta))
    P = (D / 2) * theta
    Rh = A / P
    V = V_Manning(Rh, S0, n)
    return A * V
def resolver_h(S0):
    def f(h):
        return Q_calculado(h, S0) - Q_AB
    h_0 = 0.5 * D
    return fsolve(f, h_0)[0]

# Evaluación para cada punto
distancias = []
velocidades = []
tirantes_h = []
dist_acum = 0.0
for i in range(len(df_AB) - 1):
    yi = df_AB.iloc[i]["y_cm"] / 100
    yi1 = df_AB.iloc[i+1]["y_cm"] / 100
    Li = df_AB.iloc[i+1]["dist_seg_cm"] / 100
    dist_acum += Li
    S0 = (yi - yi1) / Li
    distancias.append(dist_acum)
    if S0 <= 0:
        velocidades.append(np.nan)
        tirantes_h.append(np.nan)
        continue
    h = resolver_h(S0)
    theta = 2 * np.arccos(1 - 2*h/D)
    A = (D**2 / 8) * (theta - np.sin(theta))
    P = (D / 2) * theta
    Rh = A / P
    V = V_Manning(Rh, S0, n)
    tirantes_h.append(h)
    velocidades.append(V)

# Gráfico velocidad y tirante 
fig, ax1 = plt.subplots()
l1, = ax1.plot(distancias, velocidades, label="Velocidad")
l2 = ax1.axhline(2.8, color="red", linestyle="--", label="Límite 2.8 m/s")
ax1.set_xlabel("Distancia desde A [m]")
ax1.set_ylabel("Velocidad [m/s]")
ax1.grid(True)
ax2 = ax1.twinx()
l3, = ax2.plot(distancias, tirantes_h, color="green", label="Tirante h")
ax2.set_ylabel("Tirante h [m]")
ax1.legend(handles=[l1, l2, l3], loc="best", fontsize=7)
fig.suptitle("Perfil de velocidad y tirante – Tramo AB")
fig.tight_layout()
plt.show()

# Energía potencial
energia_potencial = []
for i in range(len(df_AB) - 1):
    z = df_AB.iloc[i]["y_cm"] / 100
    energia_potencial.append(z)
# Energía cinética
energia_cinetica = []
for V in velocidades:
    if np.isnan(V):
        energia_cinetica.append(np.nan)
    else:
        energia_cinetica.append(V**2 / (2 * g))
# Pérdidas por fricción
perdidas_friccion = []
perdida_acum = 0.0
for i in range(len(df_AB) - 1):
    V = velocidades[i]
    if np.isnan(V):
        perdidas_friccion.append(np.nan)
        continue
    h = tirantes_h[i]
    theta = 2 * np.arccos(1 - 2*h/D)
    A = (D**2 / 8) * (theta - np.sin(theta))
    P = (D / 2) * theta
    Rh = A / P
    Dh = 4 * Rh
    Li = df_AB.iloc[i+1]["dist_seg_cm"] / 100
    Re = V * Dh / 1e-6
    f = friction_factor(Re=Re, eD=1.5e-6 / Dh)
    hf = f * Li / Dh * V**2 / (2 * g)
    perdida_acum += hf
    perdidas_friccion.append(perdida_acum)
# Pérdidas por singularidades (solo entrada a B)
perdidas_sing = np.zeros(len(velocidades))
VL = velocidades[-1]
if not np.isnan(VL):
    perdidas_sing[-1] += exit_normal() * VL**2 / (2 * g)
# Energía total
energia_total = []
for i in range(len(velocidades)):
    if np.isnan(velocidades[i]):
        energia_total.append(np.nan)
    else:
        E = (energia_potencial[i] + energia_cinetica[i] + perdidas_friccion[i] + perdidas_sing[i])
        energia_total.append(E)

# Gráfico balance de energía
plt.figure()
plt.plot(distancias, energia_potencial, label="Energía potencial")
plt.plot(distancias, energia_cinetica, label="Energía cinética")
plt.plot(distancias, perdidas_friccion, label="Pérdidas por fricción")
plt.plot(distancias, energia_total, label="Energía total")
plt.xlabel("Distancia desde A [m]")
plt.ylabel("Energía [m]")
plt.title("Balance de energía - Tramo AB")
plt.grid(True)
plt.legend(fontsize=9)
plt.tight_layout()
plt.show()

def resumen(nombre, arreglo):
    arreglo = np.array(arreglo, dtype=float)
    arreglo = arreglo[~np.isnan(arreglo)]
    if len(arreglo) == 0:
        print(f"{nombre}: sin datos válidos")
        return
    print(f"{nombre}:")
    print(f"  Máximo   = {np.max(arreglo):.4f}")
    print(f"  Mínimo   = {np.min(arreglo):.4f}")
    print(f"  Promedio = {np.mean(arreglo):.4f}")
    print("")
print("Resumen Tramo AB")
resumen("Velocidad [m/s]", velocidades)
resumen("Tirante h [m]", tirantes_h)
resumen("Energía potencial [m]", energia_potencial)
resumen("Energía cinética [m]", energia_cinetica)
resumen("Pérdidas por fricción [m]", perdidas_friccion)
resumen("Pérdidas por singularidades [m]", perdidas_sing)
resumen("Energía total [m]", energia_total)

# Exportar resultados 
salida = pd.DataFrame({"Distancia_acumulada_m": distancias,"Velocidad_m_s": velocidades,"Tirante_h_m": tirantes_h,
    "Energia_potencial_m": energia_potencial,"Energia_cinetica_m": energia_cinetica,"Perdidas_friccion_m": perdidas_friccion,
    "Perdidas_singularidades_m": perdidas_sing,"Energia_total_m": energia_total})
ruta_salida = directorio_script / "Resultados_Tramo_AB.xlsx"
salida.to_excel(ruta_salida,index=False,engine="openpyxl")
print(f"Archivo Excel exportado correctamente en: {ruta_salida}")

import pandas as pd
from pathlib import Path
from CoolProp.CoolProp import PropsSI
import numpy as np
import matplotlib.pyplot as plt

# Obtiene la ruta exacta de la carpeta donde está este script (.py)
directorio_script = Path(__file__).parent

# Une esa ruta con el nombre de tu archivo CSV
ruta = directorio_script / 'coordenadas_sistema.xlsx'
#ruta = directorio_script / 'coordenadas_sistema_procesados.csv'

# Lee el archivo usando la ruta absoluta que acabamos de construir
df = pd.read_excel(ruta, decimal=',')
#Para csv   ---->      df = pd.read_csv(ruta, encoding='latin-1', sep=';', decimal=',')


# Previsualización de los datos
print(df.head())





ruta_salida = directorio_script / 'coordenadas_sistema_procesados.csv'
#ruta_salida = directorio_script / 'coordenadas_sistema_procesados_2.csv'




# Guardamos el DataFrame

df.to_csv(ruta_salida, 
          sep=';',           # Separador de columnas
          decimal=',',       # Separador de decimales (estándar chileno/Excel)
          encoding='latin-1' # Para que Excel reconozca bien los caracteres
)

print(f"Archivo guardado exitosamente en: {ruta_salida}")
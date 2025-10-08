import pandas as pd

# Nombre del archivo de entrada y salida
archivo_entrada = "Planilla_Cartilla.xlsx"
archivo_salida = "cartilla_acero.csv"

# Lee el archivo original
df = pd.read_excel(archivo_entrada)

# Renombra las columnas según lo que espera el backend
df = df.rename(columns={
    'N° Orden': 'id_pedido',
    'N° de Barra': 'numero_barra',
    'Longitud total (m)': 'longitud_pieza_requerida',
    'Cantidad': 'cantidad_requerida',
    'Grupo de Ejecución': 'grupo_ejecucion'
})

# Deja solo las columnas requeridas y las que quieras conservar
columnas_requeridas = [
    'id_pedido',
    'numero_barra',
    'longitud_pieza_requerida',
    'cantidad_requerida',
    'grupo_ejecucion'
]
# Si quieres conservar otras columnas, agrégalas aquí

# Guarda el archivo convertido
df.to_csv(archivo_salida, index=False)
print(f"Archivo convertido guardado como {archivo_salida}")
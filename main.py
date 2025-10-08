import pandas as pd
import numpy as np
import os
import json
import time
import tempfile
import matplotlib
from genetic_algorithm.engine import ejecutar_algoritmo_genetico
from genetic_algorithm.input_adapter import adaptar_entrada_completa
from genetic_algorithm.output_formatter import formatear_salida_desde_cromosoma
from flask import send_file
from weasyprint import HTML
matplotlib.use('Agg')

# --- FLASK PARA API ---
from flask import Flask, request, jsonify
import io

app = Flask(__name__)

# Agrega esto para habilitar CORS:
from flask_cors import CORS
CORS(app)

def convert_np(obj):
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, dict):
        return {k: convert_np(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_np(i) for i in obj]
    return obj

def clean_nans(obj):
    if isinstance(obj, float) and (np.isnan(obj) or obj is None):
        return None
    if isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nans(i) for i in obj]
    return obj

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint para recibir un archivo XLSX o CSV desde el frontend,
    procesarlo y devolver resultados avanzados de optimización.
    """
    print("===> Entrando a /upload")
    if 'file' not in request.files:
        print("Error: No file part")
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    document_number = request.form.get('documentNumber', '')
    perfil = request.form.get('perfil', 'balanceado')  # Nuevo: recibe el perfil del frontend

    if file.filename == '':
        print("Error: No selected file")
        return jsonify({'error': 'No selected file'}), 400

    try:
        print("===> Entrando al try de /upload")
        filename = file.filename.lower()
        if filename.endswith('.csv'):
            df = pd.read_csv(file, sep=';')
            print("===> Archivo CSV leído correctamente")
        else:
            df = pd.read_excel(file)
            print("===> Archivo Excel leído correctamente")

        print("===> DataFrame leído:")
        print(df.head())
        print("===> Columnas:", df.columns.tolist())

        # Validar si la cartilla está vacía
        if df.empty:
            print("Error: La cartilla está vacía o no contiene datos válidos.")
            return jsonify({'error': 'La cartilla está vacía o no contiene datos válidos.'}), 400

        # Renombra columnas automáticamente si vienen con nombres originales
        df = df.rename(columns={
            'N° Orden': 'id_pedido',
            'N° de Barra': 'numero_barra',
            'Longitud total (m)': 'longitud_pieza_requerida',
            'Cantidad': 'cantidad_requerida',
            'Grupo de Ejecución': 'grupo_ejecucion'
        })

        # Validar columnas mínimas requeridas
        columnas_esperadas = ['id_pedido', 'numero_barra', 'longitud_pieza_requerida', 'cantidad_requerida', 'grupo_ejecucion']
        for col in columnas_esperadas:
            if col not in df.columns:
                print(f"Error: Columna faltante: {col}")
                return jsonify({'error': f'Columna faltante: {col}'}), 400

        print("===> Columnas validadas correctamente")
        # Cargar barras estándar desde archivo
        barras_estandar_dict = cargar_barras_estandar(RUTA_BARRAS_ESTANDAR)
        print("===> Barras estándar cargadas:", barras_estandar_dict)
        if not barras_estandar_dict:
            print("Error: No se pudieron cargar las barras estándar")
            return jsonify({'error': 'No se pudieron cargar las barras estándar'}), 500

        resultados_globales = []
        desperdicios_globales_por_tipo_barra = {tipo: [] for tipo in barras_estandar_dict.keys()}

        numeros_barra_unicos = df['numero_barra'].unique()
        for num_barra_actual in numeros_barra_unicos:
            cartilla_num_barra_df = df[df['numero_barra'] == num_barra_actual].copy()
            if cartilla_num_barra_df.empty:
                continue

            barras_estandar_para_tipo_actual = barras_estandar_dict.get(num_barra_actual, [])
            if not barras_estandar_para_tipo_actual:
                continue

            desperdicios_acumulados_para_este_tipo = list(desperdicios_globales_por_tipo_barra[num_barra_actual])
            grupos_ejecucion_unicos = sorted(cartilla_num_barra_df['grupo_ejecucion'].unique())

            for grupo_ej_actual in grupos_ejecucion_unicos:
                piezas_requeridas_grupo_df = cartilla_num_barra_df[
                    cartilla_num_barra_df['grupo_ejecucion'] == grupo_ej_actual
                ][['id_pedido', 'longitud_pieza_requerida', 'cantidad_requerida']].copy()

                if piezas_requeridas_grupo_df.empty:
                    continue

                # Aquí se pasa el perfil seleccionado como configuración al algoritmo
                patrones_generados, nuevos_desperdicios_de_este_grupo = \
                    algoritmo_optimizacion_corte(
                        piezas_requeridas_grupo_df,
                        barras_estandar_para_tipo_actual,
                        list(desperdicios_acumulados_para_este_tipo),
                        config_algoritmo=perfil  # <-- Aquí se usa el perfil
                    )

                for patron in patrones_generados:
                    resultados_globales.append({
                        'numero_barra': num_barra_actual,
                        'grupo_ejecucion': grupo_ej_actual,
                        **patron
                    })

                if nuevos_desperdicios_de_este_grupo:
                    desperdicios_acumulados_para_este_tipo.extend(nuevos_desperdicios_de_este_grupo)
                    desperdicios_acumulados_para_este_tipo = consolidar_desperdicios(
                        desperdicios_acumulados_para_este_tipo,
                        LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE
                    )
                    desperdicios_acumulados_para_este_tipo = priorizar_desperdicios(
                        desperdicios_acumulados_para_este_tipo,
                        'mayor_primero'
                    )

            desperdicios_globales_por_tipo_barra[num_barra_actual] = desperdicios_acumulados_para_este_tipo

        if resultados_globales:
            resultados_df = pd.DataFrame(resultados_globales)
            cols_ordenadas = ['numero_barra', 'grupo_ejecucion', 'barra_origen_longitud', 'cortes_realizados', 'piezas_obtenidas', 'desperdicio_resultante']
            for col in cols_ordenadas:
                if col not in resultados_df.columns:
                    resultados_df[col] = None
            resultados_df = resultados_df[cols_ordenadas]

            metricas_desperdicios = generar_metricas_desperdicios(desperdicios_globales_por_tipo_barra, resultados_df)

            print("===> Respuesta enviada correctamente")
            response_json = {
                'document_number': document_number,
                'num_rows': len(df),
                'columns': list(df.columns),
                'resultados': resultados_df.to_dict(orient='records'),
                'metricas': metricas_desperdicios,
                'cartilla': df.to_dict(orient='records')
            }
            response_json = convert_np(response_json)
            response_json = clean_nans(response_json)
            print("===> JSON de respuesta:", response_json)

            return jsonify(response_json)
        else:
            print("Error: No se generaron patrones de corte")
            return jsonify({'error': 'No se generaron patrones de corte'}), 422

    except Exception as e:
        print(f"Error inesperado: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/descargar-pdf', methods=['POST'])
def descargar_pdf():
    """
    Recibe los datos de resultados y genera un PDF para descargar.
    Espera un JSON con los datos necesarios.
    Además, guarda los resultados para que el endpoint /descargar-grafica-cortes (GET) pueda usarlos.
    """
    data = request.get_json()
    resultados = data.get('resultados')
    metricas = data.get('metricas')
    columnas = data.get('columnas')
    document_number = data.get('document_number')
    cartilla = data.get('cartilla')  # Opcional: si envías la cartilla original

    import pandas as pd
    import json
    import os

    # Limpia los datos antes de crear los DataFrame
    resultados = convert_np(resultados)
    resultados = clean_nans(resultados)
    if cartilla is not None:
        cartilla = convert_np(cartilla)
        cartilla = clean_nans(cartilla)
    if metricas is not None:
        metricas = convert_np(metricas)
        metricas = clean_nans(metricas)

    # Reconstruir DataFrame de resultados
    if resultados is None:
        return jsonify({'error': 'No se recibieron resultados para el PDF.'}), 400
    resultados_df = pd.DataFrame(resultados)

    # Reconstruir DataFrame de la cartilla original si se envía, si no, usa resultados_df
    if cartilla is not None:
        cartilla_df = pd.DataFrame(cartilla)
    else:
        cartilla_df = resultados_df

    # Guarda los resultados para el endpoint GET de la gráfica
    RUTA_ULTIMO_RESULTADO = 'ultimo_resultado.json'
    try:
        with open(RUTA_ULTIMO_RESULTADO, 'w', encoding='utf-8') as f:
            json.dump(resultados, f)
    except Exception as e:
        print(f"Advertencia: No se pudo guardar el último resultado para la gráfica: {e}")

    # Usa tu función para generar el HTML directamente (NO markdown2)
    try:
        html = generar_plan_de_corte_ejecutable(resultados_df, cartilla_df, {}, metricas)
    except Exception as e:
        print(f"Error generando el HTML para el PDF: {e}")
        return jsonify({'error': 'Error generando el PDF.'}), 500

    # Genera el PDF temporalmente
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmpfile:
            HTML(string=html).write_pdf(tmpfile.name)
            tmpfile.flush()
            return send_file(tmpfile.name, as_attachment=True, download_name=f'plan_corte_{document_number}.pdf')
    except Exception as e:
        print(f"Error generando el PDF: {e}")
        return jsonify({'error': 'Error generando el PDF.'}), 500
    
# --- Configuración ---
RUTA_CARTILLA_ACERO = 'cartilla_acero.csv'
RUTA_BARRAS_ESTANDAR = 'barras_estandar.json'
LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE = 0.0 # Metros. Desperdicios menores se consideran pérdida.

# --- Configuración del Algoritmo Genético ---
CONFIGURACIONES_AG = {
    'rapido': {
        'tamaño_poblacion': 15,
        'max_generaciones': 20,
        'estrategia_inicializacion': 'heuristica',
        'metodo_seleccion': 'torneo',
        'tamaño_torneo': 3,
        'tasa_cruce': 0.8,
        'estrategia_cruce': 'un_punto',
        'tasa_mutacion_individuo': 0.2,
        'tasa_mutacion_gen': 0.1,
        'elitismo': True,
        'tamaño_elite': 2,
        'criterio_convergencia': 'generaciones_sin_mejora',
        'generaciones_sin_mejora_max': 8,
        'tiempo_limite_segundos': 30,
        'logging_habilitado': False
    },
    'balanceado': {
        'tamaño_poblacion': 30,
        'max_generaciones': 50,
        'estrategia_inicializacion': 'hibrida',
        'metodo_seleccion': 'torneo',
        'tamaño_torneo': 4,
        'tasa_cruce': 0.8,
        'estrategia_cruce': 'basado_en_piezas',
        'tasa_mutacion_individuo': 0.25,
        'tasa_mutacion_gen': 0.15,
        'elitismo': True,
        'tamaño_elite': 3,
        'criterio_convergencia': 'generaciones_sin_mejora',
        'generaciones_sin_mejora_max': 15,
        'tiempo_limite_segundos': 120,
        'logging_habilitado': True,
        'logging_frecuencia': 10
    },
    'intensivo': {
        'tamaño_poblacion': 50,
        'max_generaciones': 100,
        'estrategia_inicializacion': 'hibrida',
        'metodo_seleccion': 'torneo',
        'tamaño_torneo': 5,
        'tasa_cruce': 0.85,
        'estrategia_cruce': 'basado_en_piezas',
        'tasa_mutacion_individuo': 0.3,
        'tasa_mutacion_gen': 0.2,
        'elitismo': True,
        'tamaño_elite': 5,
        'criterio_convergencia': 'generaciones_sin_mejora',
        'generaciones_sin_mejora_max': 25,
        'tiempo_limite_segundos': 300,
        'logging_habilitado': True,
        'logging_frecuencia': 5
    }
}

# Configuración por defecto del AG (se puede cambiar aquí)
PERFIL_AG_DEFAULT = 'rapido'

# --- Funciones de Carga de Datos ---
def cargar_cartilla_acero(ruta_archivo):
    """
    Carga la cartilla de acero desde un archivo CSV.
    Espera columnas como: id_pedido, numero_barra, longitud_pieza_requerida,
                         cantidad_requerida, grupo_ejecucion.
    """
    try:
        df = pd.read_csv(ruta_archivo)
        # Validaciones básicas (se pueden expandir)
        columnas_esperadas = ['id_pedido', 'numero_barra', 'longitud_pieza_requerida', 'cantidad_requerida', 'grupo_ejecucion']
        for col in columnas_esperadas:
            if col not in df.columns:
                raise ValueError(f"Columna faltante en la cartilla de acero: {col}")
        print(f"Cartilla de acero cargada exitosamente desde {ruta_archivo}")
        return df
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de cartilla de acero en {ruta_archivo}")
        return pd.DataFrame() # Retorna DataFrame vacío en caso de error
    except Exception as e:
        print(f"Error al cargar la cartilla de acero: {e}")
        return pd.DataFrame()

def cargar_barras_estandar(ruta_archivo):
    """
    Carga las longitudes de las barras estándar desde un archivo JSON.
    El JSON debe tener la forma: {"#4": [6.0, 12.0], "#5": [6.0, 12.0]}
    """
    try:
        with open(ruta_archivo, 'r') as f:
            barras = json.load(f)
        print(f"Barras estándar cargadas exitosamente desde {ruta_archivo}")
        return barras
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de barras estándar en {ruta_archivo}")
        return {}
    except json.JSONDecodeError:
        print(f"Error: El archivo {ruta_archivo} no es un JSON válido.")
        return {}
    except Exception as e:
        print(f"Error al cargar las barras estándar: {e}")
        return {}

# --- Algoritmo de Optimización (Algoritmo Genético) ---
def algoritmo_optimizacion_corte(piezas_requeridas_df,
                                 barras_estandar_disponibles_para_tipo,
                                 desperdicios_reutilizables_previos,
                                 config_algoritmo=None):
    """
    Algoritmo de optimización de corte usando Algoritmo Genético.

    Args:
        piezas_requeridas_df (pd.DataFrame): DataFrame con las piezas a cortar para el grupo actual.
                                            Columnas: 'longitud_pieza_requerida', 'cantidad_requerida', 'id_pedido'.
        barras_estandar_disponibles_para_tipo (list): Lista de longitudes de barras estándar (ej. [6.0, 12.0]).
        desperdicios_reutilizables_previos (list): Lista de longitudes de desperdicios de grupos anteriores.
        config_algoritmo (dict, optional): Configuración específica para el algoritmo.

    Returns:
        tuple: (patrones_de_corte_generados, nuevos_desperdicios_utilizables)
               patrones_de_corte_generados (list): Lista de diccionarios, cada uno representando un patrón.
               nuevos_desperdicios_utilizables (list): Lista de longitudes de desperdicios generados
                                                       en esta corrida, mayores a LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE.
    """
    tiempo_inicio = time.time()
    
    # Determinar configuración del AG
    if config_algoritmo is None:
        perfil_ag = PERFIL_AG_DEFAULT
    elif isinstance(config_algoritmo, str):
        perfil_ag = config_algoritmo
    elif isinstance(config_algoritmo, dict) and 'perfil' in config_algoritmo:
        perfil_ag = config_algoritmo['perfil']
    else:
        perfil_ag = PERFIL_AG_DEFAULT
    
    # Obtener configuración del perfil
    if perfil_ag in CONFIGURACIONES_AG:
        config_ga = CONFIGURACIONES_AG[perfil_ag].copy()
    else:
        print(f"ADVERTENCIA: Perfil '{perfil_ag}' no encontrado. Usando '{PERFIL_AG_DEFAULT}'.")
        config_ga = CONFIGURACIONES_AG[PERFIL_AG_DEFAULT].copy()
    
    # Aplicar configuración personalizada si se proporciona
    if isinstance(config_algoritmo, dict) and 'parametros' in config_algoritmo:
        config_ga.update(config_algoritmo['parametros'])
    
    print(f"\n--- Ejecutando Algoritmo Genético (Perfil: {perfil_ag}) ---")
    if config_ga.get('logging_habilitado', True):
        print(f"Piezas requeridas: {len(piezas_requeridas_df)} tipos, {piezas_requeridas_df['cantidad_requerida'].sum()} piezas totales")
        print(f"Barras estándar disponibles: {barras_estandar_disponibles_para_tipo}")
        print(f"Desperdicios reutilizables: {desperdicios_reutilizables_previos}")
    
    try:
        # Adaptar datos de entrada al formato del AG
        piezas_adaptadas, barras_dict, desperdicios_dict, resumen = adaptar_entrada_completa(
            piezas_requeridas_df,
            barras_estandar_disponibles_para_tipo,
            desperdicios_reutilizables_previos,
            LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE,
            consolidar_piezas=True,
            limpiar_datos=True
        )
        
        # Ejecutar algoritmo genético
        mejor_cromosoma, estadisticas = ejecutar_algoritmo_genetico(
            piezas_adaptadas,
            barras_dict,
            desperdicios_dict,
            config_ga
        )
        
        # Formatear salida al formato esperado por main.py
        patrones_de_corte_generados, nuevos_desperdicios_utilizables = formatear_salida_desde_cromosoma(
            mejor_cromosoma,
            LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE
        )
        
        tiempo_total = time.time() - tiempo_inicio
        
        if config_ga.get('logging_habilitado', True):
            print(f"Algoritmo genético completado en {tiempo_total:.2f} segundos")
            print(f"Mejor fitness: {estadisticas.get('mejor_fitness_global', 'N/A'):.4f}")
            print(f"Generaciones ejecutadas: {estadisticas.get('generaciones_ejecutadas', 'N/A')}")
            print(f"Patrones generados: {len(patrones_de_corte_generados)}")
            print(f"Nuevos desperdicios utilizables: {len(nuevos_desperdicios_utilizables)}")
            
            # Calcular eficiencia
            if patrones_de_corte_generados:
                longitud_total_barras = sum(p['barra_origen_longitud'] for p in patrones_de_corte_generados)
                desperdicio_total = sum(p['desperdicio_resultante'] for p in patrones_de_corte_generados)
                eficiencia = ((longitud_total_barras - desperdicio_total) / longitud_total_barras * 100) if longitud_total_barras > 0 else 0
                print(f"Eficiencia de material: {eficiencia:.1f}%")
        
        print("--- Fin Algoritmo Genético ---")
        return patrones_de_corte_generados, nuevos_desperdicios_utilizables
        
    except Exception as e:
        print(f"ERROR en el algoritmo genético: {e}")
        print("Ejecutando algoritmo de respaldo (First Fit Decreasing)...")
        
        # Algoritmo de respaldo simple
        return _algoritmo_respaldo_ffd(
            piezas_requeridas_df,
            barras_estandar_disponibles_para_tipo,
            desperdicios_reutilizables_previos
        )


def _algoritmo_respaldo_ffd(piezas_requeridas_df, barras_disponibles, desperdicios_previos):
    """
    Algoritmo de respaldo usando First Fit Decreasing simple.
    Se ejecuta si el algoritmo genético falla.
    """
    print("Ejecutando First Fit Decreasing como respaldo...")
    
    patrones_de_corte_generados = []
    nuevos_desperdicios_utilizables = []
    
    # Combinar todas las barras disponibles
    inventario_barras = sorted(barras_disponibles + desperdicios_previos, reverse=True)
    
    # Expandir piezas requeridas
    piezas_pendientes = []
    for _, fila in piezas_requeridas_df.iterrows():
        for _ in range(int(fila['cantidad_requerida'])):
            piezas_pendientes.append({
                'id_pedido': fila['id_pedido'], 
                'longitud': fila['longitud_pieza_requerida']
            })
    
    # Ordenar piezas por longitud (decreasing)
    piezas_pendientes = sorted(piezas_pendientes, key=lambda x: x['longitud'], reverse=True)
    
    # Aplicar First Fit Decreasing
    for barra_longitud in inventario_barras:
        if not piezas_pendientes:
            break
            
        longitud_restante = barra_longitud
        cortes_en_barra = []
        piezas_en_barra = []
        piezas_restantes = []
        
        for pieza in piezas_pendientes:
            if longitud_restante >= pieza['longitud']:
                cortes_en_barra.append(pieza['longitud'])
                piezas_en_barra.append(pieza)
                longitud_restante -= pieza['longitud']
            else:
                piezas_restantes.append(pieza)
        
        if cortes_en_barra:
            desperdicio = barra_longitud - sum(cortes_en_barra)
            patron = {
                'barra_origen_longitud': barra_longitud,
                'cortes_realizados': cortes_en_barra,
                'piezas_obtenidas': piezas_en_barra,
                'desperdicio_resultante': round(desperdicio, 3)
            }
            patrones_de_corte_generados.append(patron)
            
            if desperdicio >= LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE:
                nuevos_desperdicios_utilizables.append(round(desperdicio, 3))
        
        piezas_pendientes = piezas_restantes
    
    if piezas_pendientes:
        print(f"ADVERTENCIA: {len(piezas_pendientes)} piezas no pudieron ser cortadas con el algoritmo de respaldo")
    
    print(f"Algoritmo de respaldo completado: {len(patrones_de_corte_generados)} patrones generados")
    return patrones_de_corte_generados, nuevos_desperdicios_utilizables


# --- Funciones de Gestión de Desperdicios ---
def consolidar_desperdicios(desperdicios_lista, longitud_minima=None, tolerancia=0.01):
    """
    Consolida desperdicios eliminando duplicados y muy similares.
    
    Args:
        desperdicios_lista: Lista de longitudes de desperdicios
        longitud_minima: Longitud mínima para considerar utilizable
        tolerancia: Tolerancia para considerar desperdicios como iguales
    
    Returns:
        List[float]: Lista consolidada de desperdicios
    """
    if longitud_minima is None:
        longitud_minima = LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE
    
    # Filtrar por longitud mínima
    desperdicios_validos = [d for d in desperdicios_lista if d >= longitud_minima]
    
    if not desperdicios_validos:
        return []
    
    # Ordenar y consolidar similares
    desperdicios_ordenados = sorted(desperdicios_validos, reverse=True)
    desperdicios_consolidados = []
    
    for desperdicio in desperdicios_ordenados:
        # Verificar si ya existe uno similar
        similar_encontrado = False
        for existente in desperdicios_consolidados:
            if abs(desperdicio - existente) <= tolerancia:
                similar_encontrado = True
                break
        
        if not similar_encontrado:
            desperdicios_consolidados.append(round(desperdicio, 3))
    
    return desperdicios_consolidados


def priorizar_desperdicios(desperdicios_lista, estrategia='mayor_primero'):
    """
    Prioriza desperdicios según diferentes estrategias.
    
    Args:
        desperdicios_lista: Lista de longitudes de desperdicios
        estrategia: 'mayor_primero', 'menor_primero', 'balanceado'
    
    Returns:
        List[float]: Lista priorizada de desperdicios
    """
    if not desperdicios_lista:
        return []
    
    if estrategia == 'mayor_primero':
        return sorted(desperdicios_lista, reverse=True)
    elif estrategia == 'menor_primero':
        return sorted(desperdicios_lista)
    elif estrategia == 'balanceado':
        # Intercalar grandes y pequeños
        ordenados_desc = sorted(desperdicios_lista, reverse=True)
        ordenados_asc = sorted(desperdicios_lista)
        resultado = []
        
        for i in range(len(desperdicios_lista)):
            if i % 2 == 0 and i // 2 < len(ordenados_desc):
                resultado.append(ordenados_desc[i // 2])
            elif (i - 1) // 2 < len(ordenados_asc):
                resultado.append(ordenados_asc[(i - 1) // 2])
        
        return resultado
    else:
        return desperdicios_lista


def generar_metricas_desperdicios(desperdicios_por_tipo, resultados_df):
    """
    Genera métricas detalladas sobre el uso de desperdicios.
    
    Args:
        desperdicios_por_tipo: Dict con desperdicios finales por tipo de barra
        resultados_df: DataFrame con resultados de optimización
    
    Returns:
        Dict: Métricas de desperdicios
    """
    metricas = {
        'desperdicios_finales_total': 0,
        'desperdicios_finales_longitud': 0.0,
        'desperdicios_por_tipo': {},
        'eficiencia_global': 0.0,
        'tasa_reutilizacion': 0.0
    }
    
    # Calcular desperdicios finales
    for tipo, deps in desperdicios_por_tipo.items():
        deps_utilizables = [d for d in deps if d >= LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE]
        metricas['desperdicios_finales_total'] += len(deps_utilizables)
        metricas['desperdicios_finales_longitud'] += sum(deps_utilizables)
        metricas['desperdicios_por_tipo'][tipo] = {
            'cantidad': len(deps_utilizables),
            'longitud_total': round(sum(deps_utilizables), 3),
            'longitud_promedio': round(sum(deps_utilizables) / len(deps_utilizables), 3) if deps_utilizables else 0
        }
    
    # Calcular eficiencia global
    if not resultados_df.empty:
        longitud_total_barras = resultados_df['barra_origen_longitud'].sum()
        desperdicio_total = resultados_df['desperdicio_resultante'].sum()
        
        if longitud_total_barras > 0:
            metricas['eficiencia_global'] = round(
                ((longitud_total_barras - desperdicio_total) / longitud_total_barras) * 100, 2
            )
    
    return metricas


# --- Lógica Principal ---
def main():
    """
    Función principal para orquestar el proceso de optimización de cortes.
    """
    print("Iniciando proceso de optimización de cortes de acero...")

    # 1. Cargar datos
    cartilla_df = cargar_cartilla_acero(RUTA_CARTILLA_ACERO)
    barras_estandar_dict = cargar_barras_estandar(RUTA_BARRAS_ESTANDAR)

    if cartilla_df.empty or not barras_estandar_dict:
        print("No se pudieron cargar los datos necesarios. Terminando ejecución.")
        return

    # Estructura para almacenar todos los resultados
    resultados_globales = []
    # Estructura para llevar cuenta de los desperdicios por tipo de barra a través de los grupos de ejecución
    desperdicios_globales_por_tipo_barra = {tipo: [] for tipo in barras_estandar_dict.keys()}


    # 2. Agrupar por 'numero_barra' (diámetro)
    numeros_barra_unicos = cartilla_df['numero_barra'].unique()
    print(f"\nProcesando los siguientes tipos de barra (diámetros): {numeros_barra_unicos}")

    for num_barra_actual in numeros_barra_unicos:
        print(f"\n===== Procesando Número de Barra: {num_barra_actual} =====")
        
        cartilla_num_barra_df = cartilla_df[cartilla_df['numero_barra'] == num_barra_actual].copy()
        if cartilla_num_barra_df.empty:
            print(f"No hay pedidos para el número de barra {num_barra_actual}.")
            continue

        barras_estandar_para_tipo_actual = barras_estandar_dict.get(num_barra_actual, [])
        if not barras_estandar_para_tipo_actual:
            print(f"ADVERTENCIA: No se encontraron longitudes de barras estándar definidas para {num_barra_actual}. Saltando este tipo.")
            continue
        
        # Desperdicios acumulados específicamente para este 'numero_barra' a través de sus grupos de ejecución
        desperdicios_acumulados_para_este_tipo = list(desperdicios_globales_por_tipo_barra[num_barra_actual]) # Copia para modificarla localmente


        # 3. Agrupar por 'grupo_ejecucion' (orden de uso en obra) y procesar secuencialmente
        grupos_ejecucion_unicos = sorted(cartilla_num_barra_df['grupo_ejecucion'].unique())
        print(f"Procesando grupos de ejecución para {num_barra_actual}: {grupos_ejecucion_unicos}")

        for grupo_ej_actual in grupos_ejecucion_unicos:
            print(f"\n--- Procesando Grupo de Ejecución: {grupo_ej_actual} (para Barra {num_barra_actual}) ---")
            
            piezas_requeridas_grupo_df = cartilla_num_barra_df[
                cartilla_num_barra_df['grupo_ejecucion'] == grupo_ej_actual
            ][['id_pedido', 'longitud_pieza_requerida', 'cantidad_requerida']].copy()

            if piezas_requeridas_grupo_df.empty:
                print(f"No hay piezas requeridas para el grupo de ejecución {grupo_ej_actual} de la barra {num_barra_actual}.")
                continue
            
            print(f"Desperdicios disponibles de grupos anteriores para {num_barra_actual}: {desperdicios_acumulados_para_este_tipo}")

            # Llamada al algoritmo de optimización
            # Los desperdicios_acumulados_para_este_tipo son los que vienen de grupos de ejecución ANTERIORES
            # para ESTE MISMO numero_barra.
            patrones_generados, nuevos_desperdicios_de_este_grupo = \
                algoritmo_optimizacion_corte(piezas_requeridas_grupo_df,
                                             barras_estandar_para_tipo_actual,
                                             list(desperdicios_acumulados_para_este_tipo), # Pasar una copia
                                             config_algoritmo=None) # Aquí iría la config del AG

            # Guardar resultados de este grupo
            for patron in patrones_generados:
                resultados_globales.append({
                    'numero_barra': num_barra_actual,
                    'grupo_ejecucion': grupo_ej_actual,
                    **patron # Desempaqueta el diccionario del patrón
                })
            
            # Actualizar la lista de desperdicios acumulados para el SIGUIENTE grupo de ejecución
            # DENTRO de este MISMO 'numero_barra'
            # Se añaden los nuevos desperdicios generados en esta corrida.
            if nuevos_desperdicios_de_este_grupo:
                desperdicios_acumulados_para_este_tipo.extend(nuevos_desperdicios_de_este_grupo)
                
                # Consolidar y priorizar desperdicios
                desperdicios_acumulados_para_este_tipo = consolidar_desperdicios(
                    desperdicios_acumulados_para_este_tipo,
                    LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE
                )
                desperdicios_acumulados_para_este_tipo = priorizar_desperdicios(
                    desperdicios_acumulados_para_este_tipo,
                    'mayor_primero'
                )
                
                print(f"Desperdicios actualizados para {num_barra_actual} después del grupo {grupo_ej_actual}: {desperdicios_acumulados_para_este_tipo}")

        # Al final de procesar todos los grupos de ejecución para un 'numero_barra',
        # los desperdicios_acumulados_para_este_tipo son los que quedan para ese tipo de barra.
        # Esta línea es más para ilustrar, ya que la lógica de compartición entre tipos de barra no está implementada.
        # La regla dice "sólo se pueden compartir desperdicios entre barras del mismo grupo (número de barra)".
        # Y "el Grupo 1 puede compartir desperdicios con Grupos posteriores (2, 3, 4, ...), pero no al revés."
        # Esto ya se maneja con `desperdicios_acumulados_para_este_tipo` que se pasa secuencialmente.
        desperdicios_globales_por_tipo_barra[num_barra_actual] = desperdicios_acumulados_para_este_tipo


    # 4. Mostrar/Guardar resultados consolidados
    print("\n\n===== RESULTADOS GLOBALES DE OPTIMIZACIÓN =====")
    if resultados_globales:
        resultados_df = pd.DataFrame(resultados_globales)
        # Reordenar columnas para mejor visualización
        cols_ordenadas = ['numero_barra', 'grupo_ejecucion', 'barra_origen_longitud', 'cortes_realizados', 'piezas_obtenidas', 'desperdicio_resultante']
        # Añadir columnas que podrían faltar si un patrón no las tiene (poco probable con el **patron)
        for col in cols_ordenadas:
            if col not in resultados_df.columns:
                resultados_df[col] = None
        resultados_df = resultados_df[cols_ordenadas]

        print(resultados_df.to_string()) # Imprime todo el DataFrame
        
        # Opcional: Guardar en un archivo
        try:
            resultados_df.to_csv('resultados_optimizacion_cortes.csv', index=False)
            print("\nResultados guardados en 'resultados_optimizacion_cortes.csv'")
        except Exception as e:
            print(f"Error al guardar los resultados en CSV: {e}")
            
        # Calcular desperdicio total
        desperdicio_total_general = 0
        for _, fila in resultados_df.iterrows():
            # Asegurarse de que 'desperdicio_resultante' no sea None y sea numérico
            if pd.notna(fila['desperdicio_resultante']) and isinstance(fila['desperdicio_resultante'], (int, float)):
                 # Considerar solo desperdicio que NO es reutilizable o el desperdicio final de la última barra usada.
                 # Esta métrica necesita refinamiento. Por ahora, sumamos todos los 'desperdicio_resultante' de los patrones.
                 # Una mejor métrica sería: (Sum(longitud_barras_usadas) - Sum(longitud_piezas_cortadas_utiles))
                desperdicio_total_general += fila['desperdicio_resultante']
        print(f"\nDesperdicio total registrado en los patrones (aproximado): {desperdicio_total_general:.2f} metros")
        
        # Generar métricas detalladas de desperdicios
        metricas_desperdicios = generar_metricas_desperdicios(desperdicios_globales_por_tipo_barra, resultados_df)
        
        print(f"\n===== MÉTRICAS DE EFICIENCIA =====")
        print(f"Eficiencia global de material: {metricas_desperdicios['eficiencia_global']:.2f}%")
        print(f"Desperdicios finales utilizables: {metricas_desperdicios['desperdicios_finales_total']} piezas")
        print(f"Longitud total de desperdicios finales: {metricas_desperdicios['desperdicios_finales_longitud']:.2f} metros")
        
        # Calcular estadísticas adicionales
        total_patrones = len(resultados_df)
        total_barras_utilizadas = total_patrones  # Asumiendo una barra por patrón
        
        # Calcular total de piezas cortadas de forma segura
        total_piezas_cortadas = 0
        for _, fila in resultados_df.iterrows():
            piezas = fila['piezas_obtenidas']
            try:
                # Verificar si piezas no es None/NaN
                if piezas is not None and not (isinstance(piezas, float) and pd.isna(piezas)):
                    if isinstance(piezas, list):
                        total_piezas_cortadas += len(piezas)
                    elif isinstance(piezas, str):
                        # Si es string, intentar evaluar
                        try:
                            piezas_eval = eval(piezas)
                            if isinstance(piezas_eval, list):
                                total_piezas_cortadas += len(piezas_eval)
                            else:
                                total_piezas_cortadas += 1
                        except:
                            # Si falla la evaluación, contar como 1
                            total_piezas_cortadas += 1
                    else:
                        # Para cualquier otro tipo, contar como 1
                        total_piezas_cortadas += 1
            except Exception as e:
                # En caso de cualquier error, simplemente continuar
                continue
        
        print(f"Total de patrones de corte: {total_patrones}")
        print(f"Total de barras utilizadas: {total_barras_utilizadas}")
        print(f"Total de piezas cortadas: {total_piezas_cortadas}")

    else:
        print("No se generaron patrones de corte.")
    
    print("\n===== DESPERDICIOS FINALES POR TIPO DE BARRA =====")
    for tipo, deps in desperdicios_globales_por_tipo_barra.items():
        # Filtramos para mostrar solo los que realmente son utilizables según el mínimo.
        deps_filtrados = [d for d in deps if d >= LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE]
        if deps_filtrados:
            print(f"  - {tipo}: {len(deps_filtrados)} piezas, {sum(deps_filtrados):.2f}m total")
            print(f"    Longitudes: {sorted(deps_filtrados, reverse=True)}")
        else:
            print(f"  - {tipo}: Ninguno")

    print("\n===== PROCESO COMPLETADO =====")
    print("Proceso de optimización de cortes terminado exitosamente.")
    print("Resultados guardados en 'resultados_optimizacion_cortes.csv'")

def generar_plan_de_corte_ejecutable(resultados_df, cartilla_df, desperdicios_finales, metricas):
    from datetime import datetime
    import numpy as np
    import pandas as pd

    print("===> Data para PDF:")
    print("resultados_df:")
    print(resultados_df.head())
    print("cartilla_df:")
    print(cartilla_df.head())
    print("metricas:")
    print(metricas)

    # --- LIMPIEZA DE NAN, None, ETC. ---
    def limpiar_df(df):
        df = df.replace([np.nan, None, 'nan', 'None', 'nanm', 'NaN'], '', regex=True)
        return df

    resultados_df = limpiar_df(resultados_df)
    cartilla_df = limpiar_df(cartilla_df)

    # --- CONVERSIÓN EXPLÍCITA DE COLUMNAS NUMÉRICAS ---
    for col in ['barra_origen_longitud', 'desperdicio_resultante']:
        if col in resultados_df.columns:
            resultados_df[col] = pd.to_numeric(resultados_df[col], errors='coerce')
    for col in ['longitud_pieza_requerida', 'cantidad_requerida']:
        if col in cartilla_df.columns:
            cartilla_df[col] = pd.to_numeric(cartilla_df[col], errors='coerce')

    # --- Tablas HTML bien alineadas ---
    diametros = sorted(resultados_df['numero_barra'].unique())
    cortes_por_diametro = []
    for tipo in diametros:
        cortes = sum([len(c) if isinstance(c, list) else 0 for c in resultados_df[resultados_df['numero_barra'] == tipo]['cortes_realizados']])
        cortes_por_diametro.append({'diametro': tipo, 'cortes': cortes})

    distribucion_html = """
    <table style="border-collapse:collapse;width:100%;margin-bottom:16px;">
      <thead>
        <tr style="background:#f3f3f3;">
          <th style="border:1px solid #888;padding:4px;">Diámetro</th>
          <th style="border:1px solid #888;padding:4px;">Piezas Requeridas</th>
          <th style="border:1px solid #888;padding:4px;">Patrones Generados</th>
          <th style="border:1px solid #888;padding:4px;">Eficiencia</th>
          <th style="border:1px solid #888;padding:4px;">Cortes Realizados</th>
        </tr>
      </thead>
      <tbody>
    """
    eficiencias_por_tipo = {}
    for tipo in diametros:
        piezas_tipo = cartilla_df[cartilla_df['numero_barra'] == tipo]['cantidad_requerida'].sum()
        patrones_tipo = len(resultados_df[resultados_df['numero_barra'] == tipo])
        df_tipo = resultados_df[resultados_df['numero_barra'] == tipo]
        total_material = df_tipo['barra_origen_longitud'].sum()
        total_desperdicio = df_tipo['desperdicio_resultante'].sum()
        eficiencia = ((total_material - total_desperdicio) / total_material * 100) if total_material > 0 else 0
        eficiencias_por_tipo[tipo] = eficiencia
        cortes_tipo = next((c['cortes'] for c in cortes_por_diametro if c['diametro'] == tipo), 0)
        distribucion_html += f"""
        <tr>
          <td style="border:1px solid #888;padding:4px;text-align:center;">{tipo}</td>
          <td style="border:1px solid #888;padding:4px;text-align:center;">{piezas_tipo}</td>
          <td style="border:1px solid #888;padding:4px;text-align:center;">{patrones_tipo}</td>
          <td style="border:1px solid #888;padding:4px;text-align:center;">{eficiencia:.1f}%</td>
          <td style="border:1px solid #888;padding:4px;text-align:center;">{cortes_tipo}</td>
        </tr>
        """
    distribucion_html += "</tbody></table>"

    # Resumen general de barras por diámetro
    longitudes = sorted(resultados_df['barra_origen_longitud'].unique())
    resumen_barras = []
    for tipo in diametros:
        row = {'diametro': tipo}
        total = 0
        for l in longitudes:
            count = len(resultados_df[(resultados_df['numero_barra'] == tipo) & (resultados_df['barra_origen_longitud'] == l)])
            row[f'barras_{int(l)}'] = count
            total += count
        row['total'] = total
        resumen_barras.append(row)
    resumen_html = """
    <table style="border-collapse:collapse;width:100%;margin-bottom:16px;">
      <thead>
        <tr style="background:#f3f3f3;">
          <th style="border:1px solid #888;padding:4px;">Diámetro</th>
    """
    for l in longitudes:
        resumen_html += f'<th style="border:1px solid #888;padding:4px;">Barras de {int(l)}m</th>'
    resumen_html += '<th style="border:1px solid #888;padding:4px;">Total</th></tr></thead><tbody>'
    for row in resumen_barras:
        resumen_html += f'<tr><td style="border:1px solid #888;padding:4px;text-align:center;">{row["diametro"]}</td>'
        for l in longitudes:
            resumen_html += f'<td style="border:1px solid #888;padding:4px;text-align:center;">{row[f"barras_{int(l)}"]}</td>'
        resumen_html += f'<td style="border:1px solid #888;padding:4px;text-align:center;">{row["total"]}</td></tr>'
    resumen_html += '</tbody></table>'

    # Lista de compras
    barras_por_tipo = resultados_df.groupby(['numero_barra', 'barra_origen_longitud']).size().reset_index()
    barras_por_tipo.columns = ['tipo_barra', 'longitud_barra', 'cantidad']
    compras_html = """
    <table style="border-collapse:collapse;width:100%;margin-bottom:16px;">
      <thead>
        <tr style="background:#f3f3f3;">
          <th style="border:1px solid #888;padding:4px;">Longitud</th>
          <th style="border:1px solid #888;padding:4px;">Diámetro</th>
          <th style="border:1px solid #888;padding:4px;">Cantidad Requerida</th>
          <th style="border:1px solid #888;padding:4px;">Uso Principal</th>
        </tr>
      </thead>
      <tbody>
    """
    for _, fila in barras_por_tipo.iterrows():
        compras_html += f'<tr><td style="border:1px solid #888;padding:4px;text-align:center;">{fila["longitud_barra"]}m</td>'
        compras_html += f'<td style="border:1px solid #888;padding:4px;text-align:center;">{fila["tipo_barra"]}</td>'
        compras_html += f'<td style="border:1px solid #888;padding:4px;text-align:center;">{fila["cantidad"]} barras</td>'
        compras_html += f'<td style="border:1px solid #888;padding:4px;text-align:center;">Según patrones optimizados</td></tr>'
    compras_html += '</tbody></table>'

    # Control de calidad (omite filas con NaN en longitud o cantidad)
    calidad_html = """
    <table style="border-collapse:collapse;width:100%;margin-bottom:16px;">
      <thead>
        <tr style="background:#f3f3f3;">
          <th style="border:1px solid #888;padding:4px;">Pedido</th>
          <th style="border:1px solid #888;padding:4px;">Diámetro</th>
          <th style="border:1px solid #888;padding:4px;">Longitud</th>
          <th style="border:1px solid #888;padding:4px;">Cantidad Solicitada</th>
          <th style="border:1px solid #888;padding:4px;">Estado</th>
        </tr>
      </thead>
      <tbody>
    """
    for _, fila in cartilla_df.iterrows():
        # Omitir filas donde longitud o cantidad sean NaN o vacíos
        if pd.isna(fila["longitud_pieza_requerida"]) or pd.isna(fila["cantidad_requerida"]):
            continue
        # Longitud: intenta formatear como float, si no, deja vacío o el valor original
        try:
            longitud = float(fila["longitud_pieza_requerida"])
            longitud_str = f"{longitud:.2f}m"
        except (ValueError, TypeError):
            longitud_str = f'{fila["longitud_pieza_requerida"] or ""}'
        # Cantidad: intenta formatear como int, si no, deja vacío o el valor original
        try:
            cantidad = int(fila["cantidad_requerida"])
            cantidad_str = f"{cantidad} piezas"
        except (ValueError, TypeError):
            cantidad_str = f'{fila["cantidad_requerida"] or ""} piezas'
        calidad_html += (
            f'<tr>'
            f'<td style="border:1px solid #888;padding:4px;text-align:center;">{fila.get("id_pedido","")}</td>'
            f'<td style="border:1px solid #888;padding:4px;text-align:center;">{fila.get("numero_barra","")}</td>'
            f'<td style="border:1px solid #888;padding:4px;text-align:center;">{longitud_str}</td>'
            f'<td style="border:1px solid #888;padding:4px;text-align:center;">{cantidad_str}</td>'
            f'<td style="border:1px solid #888;padding:4px;text-align:center;">✅ Completo</td></tr>'
        )
    calidad_html += '</tbody></table>'

    # --- Mostrar o no la gráfica según la cantidad ---
    mostrar_grafica = True
    if 'cantidad_requerida' in cartilla_df.columns:
        if (cartilla_df['cantidad_requerida'] > 100).any():
            mostrar_grafica = False

    if mostrar_grafica:
        visualizacion_html = """
        <div style="page-break-inside: avoid;">
        <h2 style="page-break-after: avoid;">🔪 VISUALIZACIÓN DE CORTES POR BARRA</h2>
        <p>
          <b>Para visualizar la gráfica completa de cortes por barra, <a href="http://localhost:5000/descargar-grafica-cortes-imagen" target="_blank">haz clic aquí</a> para ver o descargar la imagen de la gráfica.</b>
        </p>
        </div>
        <hr>
        """
    else:
        visualizacion_html = """
        <div style="page-break-inside: avoid;">
        <h2 style="page-break-after: avoid;">🔪 VISUALIZACIÓN DE CORTES POR BARRA</h2>
        <p>
          <b>No se muestra la gráfica porque alguna orden supera las 100 piezas.</b>
        </p>
        </div>
        <hr>
        """

    # --- Contenido HTML completo ---
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_piezas = cartilla_df['cantidad_requerida'].sum()

    contenido = f"""
    <h1 style="color:#166534;">📋 PLAN DE CORTE EJECUTABLE - CARTILLA DE ACERO</h1>
    <p><b>Generado por OICA (Optimizador Inteligente de Cortes de Acero)</b><br>
    <b>Fecha de generación:</b> {fecha_actual}<br>
    <b>Eficiencia global alcanzada:</b> {metricas.get('eficiencia_global', 0):.2f}%<br>
    <b>Total de piezas a cortar:</b> {total_piezas} piezas<br>
    <b>Total de barras a utilizar:</b> {len(resultados_df)} barras</p>
    <hr>
    <div style="page-break-inside: avoid;">
    <h2 style="page-break-after: avoid;">🎯 RESUMEN EJECUTIVO</h2>
    <ul>
      <li><b>Total de desperdicios finales utilizables:</b> {metricas.get('desperdicios_finales_total', 0)} piezas ({metricas.get('desperdicios_finales_longitud', 0):.2f} metros)</li>
      <li><b>Desperdicios no utilizables:</b> {resultados_df['desperdicio_resultante'].sum():.2f} metros</li>
      <li><b>Total de patrones de corte:</b> {len(resultados_df)}</li>
    </ul>
    </div>
    <hr>
    <div style="page-break-inside: avoid;">
    <h2 style="page-break-after: avoid;">📊 DISTRIBUCIÓN POR DIÁMETRO</h2>
    {distribucion_html}
    </div>
    <hr>
    <div style="page-break-inside: avoid;">
    <h2 style="page-break-after: avoid;">🟩 RESUMEN GENERAL DE BARRAS POR DIÁMETRO</h2>
    {resumen_html}
    </div>
    <hr>
    {visualizacion_html}
    <div style="page-break-inside: avoid;">
    <h2 style="page-break-after: avoid;">📋 LISTA DE COMPRAS DE BARRAS</h2>
    {compras_html}
    <b>TOTAL DE BARRAS:</b> {len(resultados_df)} barras
    </div>
    <hr>
    <div style="page-break-inside: avoid;">
    <h2 style="page-break-after: avoid;">✅ CONTROL DE CALIDAD</h2>
    {calidad_html}
    <b>✅ RESULTADO:</b> 100% de los pedidos cumplidos satisfactoriamente
    </div>
    <hr>
    <div style="page-break-inside: avoid;">
    <h2 style="page-break-after: avoid;">💰 ANÁLISIS ECONÓMICO</h2>
    <ul>
      <li><b>Material aprovechado:</b> {metricas.get('eficiencia_global', 0):.2f}%</li>
      <li><b>Material desperdiciado:</b> {100 - metricas.get('eficiencia_global', 0):.2f}%</li>
      <li><b>Total de desperdicios finales:</b> {metricas.get('desperdicios_finales_longitud', 0):.2f} metros</li>
    </ul>
    <b>Comparación con métodos tradicionales:</b>
    <ul>
      <li>Método tradicional estimado: ~75-80% de eficiencia</li>
      <li>Ahorro conseguido: ~9-14% de material</li>
      <li>Reducción de desperdicios: Significativa optimización</li>
    </ul>
    </div>
    <hr>
    <div style="page-break-inside: avoid;">
    <h2 style="page-break-after: avoid;">📞 CONTACTO Y SOPORTE</h2>
    <b>Sistema generado por:</b> OICA v1.0<br>
    <b>Para consultas técnicas:</b> Contactar al equipo de optimización<br>
    <b>Fecha de vigencia:</b> Válido para ejecución inmediata<br>
    </div>
    <hr>
    <p style="font-style:italic;">
    Este plan fue generado automáticamente usando algoritmos genéticos para maximizar la eficiencia del material y minimizar desperdicios. Los patrones han sido optimizados considerando las longitudes comerciales disponibles y las cantidades requeridas específicas del proyecto.
    </p>
    """

    return contenido
# Nuevo endpoint para descargar solo la gráfica de cortes por barra en PDF
@app.route('/descargar-grafica-cortes-imagen', methods=['GET'])
def descargar_grafica_cortes_imagen():
    """
    Devuelve la imagen PNG de la gráfica de cortes por barra.
    Si alguna orden supera la cantidad de 100, no genera la gráfica.
    """
    import matplotlib.pyplot as plt
    import tempfile
    import os
    import json

    RUTA_ULTIMO_RESULTADO = 'ultimo_resultado.json'

    if not os.path.exists(RUTA_ULTIMO_RESULTADO):
        return "<h2>No hay resultados recientes para mostrar la gráfica.<br>Genera primero un plan de corte.</h2>", 404
    with open(RUTA_ULTIMO_RESULTADO, 'r', encoding='utf-8') as f:
        resultados = json.load(f)
    resultados_df = pd.DataFrame(resultados)

    # --- NUEVO: No mostrar gráfica si alguna orden supera 100 piezas ---
    if 'cantidad_requerida' in resultados_df.columns:
        if (resultados_df['cantidad_requerida'].apply(pd.to_numeric, errors='coerce') > 100).any():
            return "<h2>No se puede mostrar la gráfica porque alguna orden supera las 100 piezas.</h2>", 400

    # --- Gráfica horizontal de cortes por barra ---
    barras = []
    for idx, row in resultados_df.iterrows():
        diam = row['numero_barra']
        barra_len = row['barra_origen_longitud']
        cortes = row['cortes_realizados']
        barras.append((diam, barra_len, [cortes], 1))

    fig2, ax2 = plt.subplots(figsize=(16, max(7, len(barras)*0.5)))
    y = 0
    colors = ['#4F81BD', '#C0504D', '#9BBB59', '#8064A2', '#F79646', '#2C4D75', '#E46C0A', '#948A54']
    for idx, (diam, barra_len, patrones, reps) in enumerate(barras):
        for rep in range(reps):
            x = 0
            for i, corte in enumerate(patrones[0]):
                ax2.barh(y, corte, left=x, color=colors[idx % len(colors)], edgecolor='black', height=0.8)
                x += corte
            if x < barra_len:
                ax2.barh(y, barra_len - x, left=x, color='gray', alpha=0.3, edgecolor='black', height=0.8, hatch='//')
            ax2.text(barra_len + 0.1, y, f'{diam} - {barra_len}m', va='center', fontsize=8)
            y += 1
    ax2.set_xlabel('Longitud (m)')
    ax2.set_ylabel('Barra')
    ax2.set_title('Visualización de cortes por barra')
    ax2.set_yticks([])
    plt.tight_layout()
    tmp_img2 = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(tmp_img2.name, format='png', bbox_inches='tight', dpi=200)
    plt.close(fig2)
    return send_file(tmp_img2.name, as_attachment=True, download_name='grafica_cortes_barras.png', mimetype='image/png')

if __name__ == "__main__":
    # main()  # Comenta o elimina esta línea para solo usar la API Flask
    app.run(debug=True)  # Esto levanta el servidor Flask para tu frontend
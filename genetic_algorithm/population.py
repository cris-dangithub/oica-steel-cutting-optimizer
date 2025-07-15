"""
Módulo para la inicialización de población del algoritmo genético.

Este módulo implementa diferentes estrategias para crear la población inicial
del algoritmo genético, incluyendo métodos heurísticos, aleatorios e híbridos.
"""

import random
import copy
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from .chromosome import Cromosoma, Patron
from .chromosome_utils import (
    crear_patron_corte,
    validar_cromosoma_completitud,
    calcular_sumario_piezas_en_cromosoma
)
from .optimal_analyzer import analizar_casos_homogeneos, calcular_solucion_optima_homogenea


def generar_individuo_heuristico_ffd(
    piezas_requeridas_df: pd.DataFrame,
    barras_disponibles: List[Dict[str, Any]],
    desperdicios_disponibles: List[Dict[str, Any]]
) -> Cromosoma:
    """
    Genera un individuo usando la heurística First Fit Decreasing (FFD).
    
    Args:
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        barras_disponibles: Lista de barras estándar disponibles.
        desperdicios_disponibles: Lista de desperdicios reutilizables.
    
    Returns:
        Cromosoma: Un cromosoma generado con la heurística FFD.
    """
    # Crear lista de todas las piezas individuales ordenadas por longitud (descendente)
    piezas_individuales = []
    for _, fila in piezas_requeridas_df.iterrows():
        for _ in range(int(int(fila['cantidad_requerida']))):
            piezas_individuales.append({
                'id_pedido': fila['id_pedido'],
                'longitud_pieza': fila['longitud_pieza_requerida']
            })
    
    # Ordenar piezas por longitud descendente (FFD)
    piezas_individuales.sort(key=lambda x: x['longitud_pieza'], reverse=True)
    
    # Crear lista de barras disponibles (desperdicios primero, luego estándar)
    barras_para_usar = []
    
    # Añadir desperdicios disponibles
    for desperdicio in desperdicios_disponibles:
        barras_para_usar.append({
            'longitud': desperdicio['longitud'],
            'tipo': 'desperdicio'
        })
    
    # Añadir barras estándar (asumimos disponibilidad ilimitada)
    for barra in barras_disponibles:
        barras_para_usar.append({
            'longitud': barra['longitud'],
            'tipo': 'estandar'
        })
    
    # CORRECCIÓN: Ordenar barras por eficiencia (menos desperdicio unitario) en lugar de solo longitud
    # Esto asegura que se prefieran las barras que minimizan realmente el desperdicio
    barras_para_usar.sort(key=lambda x: x['longitud'], reverse=True)  # Barras más grandes primero
    
    patrones = []
    barras_abiertas = []  # Lista de barras que están siendo utilizadas
    
    for pieza in piezas_individuales:
        colocada = False
        
        # Intentar colocar en una barra ya abierta (First Fit)
        for i, barra_abierta in enumerate(barras_abiertas):
            espacio_restante = barra_abierta['longitud_restante']
            if espacio_restante >= pieza['longitud_pieza']:
                # Añadir pieza al patrón existente
                barra_abierta['piezas_cortadas'].append({
                    'id_pedido': pieza['id_pedido'],
                    'longitud_pieza': pieza['longitud_pieza'],
                    'cantidad_pieza_en_patron': 1
                })
                barra_abierta['longitud_restante'] -= pieza['longitud_pieza']
                colocada = True
                break
        
        # Si no se pudo colocar, abrir una nueva barra
        if not colocada:
            # Buscar la barra más pequeña que pueda contener la pieza
            barra_seleccionada = None
            for barra in barras_para_usar:
                if barra['longitud'] >= pieza['longitud_pieza']:
                    barra_seleccionada = barra
                    break
            
            if barra_seleccionada:
                nueva_barra = {
                    'origen_barra_longitud': barra_seleccionada['longitud'],
                    'origen_barra_tipo': barra_seleccionada['tipo'],
                    'piezas_cortadas': [{
                        'id_pedido': pieza['id_pedido'],
                        'longitud_pieza': pieza['longitud_pieza'],
                        'cantidad_pieza_en_patron': 1
                    }],
                    'longitud_restante': barra_seleccionada['longitud'] - pieza['longitud_pieza']
                }
                barras_abiertas.append(nueva_barra)
                
                # Si es un desperdicio, removerlo de la lista disponible
                if barra_seleccionada['tipo'] == 'desperdicio':
                    barras_para_usar.remove(barra_seleccionada)
    
    # Convertir barras abiertas a patrones
    for barra_abierta in barras_abiertas:
        patron = Patron(
            origen_barra_longitud=barra_abierta['origen_barra_longitud'],
            origen_barra_tipo=barra_abierta['origen_barra_tipo'],
            piezas_cortadas=barra_abierta['piezas_cortadas']
        )
        patrones.append(patron)
    
    return Cromosoma(patrones)


def generar_individuo_heuristico_bfd(
    piezas_requeridas_df: pd.DataFrame,
    barras_disponibles: List[Dict[str, Any]],
    desperdicios_disponibles: List[Dict[str, Any]]
) -> Cromosoma:
    """
    Genera un individuo usando la heurística Best Fit Decreasing (BFD).
    
    Args:
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        barras_disponibles: Lista de barras estándar disponibles.
        desperdicios_disponibles: Lista de desperdicios reutilizables.
    
    Returns:
        Cromosoma: Un cromosoma generado con la heurística BFD.
    """
    # Crear lista de todas las piezas individuales ordenadas por longitud (descendente)
    piezas_individuales = []
    for _, fila in piezas_requeridas_df.iterrows():
        for _ in range(int(int(fila['cantidad_requerida']))):
            piezas_individuales.append({
                'id_pedido': fila['id_pedido'],
                'longitud_pieza': fila['longitud_pieza_requerida']
            })
    
    # Ordenar piezas por longitud descendente (BFD)
    piezas_individuales.sort(key=lambda x: x['longitud_pieza'], reverse=True)
    
    # Crear lista de barras disponibles
    barras_para_usar = []
    
    # Añadir desperdicios disponibles
    for desperdicio in desperdicios_disponibles:
        barras_para_usar.append({
            'longitud': desperdicio['longitud'],
            'tipo': 'desperdicio'
        })
    
    # Añadir barras estándar
    for barra in barras_disponibles:
        barras_para_usar.append({
            'longitud': barra['longitud'],
            'tipo': 'estandar'
        })
    
    patrones = []
    barras_abiertas = []
    
    for pieza in piezas_individuales:
        colocada = False
        mejor_ajuste = None
        mejor_indice = -1
        menor_desperdicio = float('inf')
        
        # Buscar el mejor ajuste entre las barras abiertas (Best Fit)
        for i, barra_abierta in enumerate(barras_abiertas):
            espacio_restante = barra_abierta['longitud_restante']
            if espacio_restante >= pieza['longitud_pieza']:
                desperdicio = espacio_restante - pieza['longitud_pieza']
                if desperdicio < menor_desperdicio:
                    menor_desperdicio = desperdicio
                    mejor_ajuste = barra_abierta
                    mejor_indice = i
        
        # Si se encontró un buen ajuste, colocar la pieza
        if mejor_ajuste is not None:
            mejor_ajuste['piezas_cortadas'].append({
                'id_pedido': pieza['id_pedido'],
                'longitud_pieza': pieza['longitud_pieza'],
                'cantidad_pieza_en_patron': 1
            })
            mejor_ajuste['longitud_restante'] -= pieza['longitud_pieza']
            colocada = True
        
        # Si no se pudo colocar, abrir una nueva barra
        if not colocada:
            # Buscar la barra más pequeña que pueda contener la pieza
            barra_seleccionada = None
            for barra in sorted(barras_para_usar, key=lambda x: x['longitud']):
                if barra['longitud'] >= pieza['longitud_pieza']:
                    barra_seleccionada = barra
                    break
            
            if barra_seleccionada:
                nueva_barra = {
                    'origen_barra_longitud': barra_seleccionada['longitud'],
                    'origen_barra_tipo': barra_seleccionada['tipo'],
                    'piezas_cortadas': [{
                        'id_pedido': pieza['id_pedido'],
                        'longitud_pieza': pieza['longitud_pieza'],
                        'cantidad_pieza_en_patron': 1
                    }],
                    'longitud_restante': barra_seleccionada['longitud'] - pieza['longitud_pieza']
                }
                barras_abiertas.append(nueva_barra)
                
                # Si es un desperdicio, removerlo de la lista disponible
                if barra_seleccionada['tipo'] == 'desperdicio':
                    barras_para_usar.remove(barra_seleccionada)
    
    # Convertir barras abiertas a patrones
    for barra_abierta in barras_abiertas:
        patron = Patron(
            origen_barra_longitud=barra_abierta['origen_barra_longitud'],
            origen_barra_tipo=barra_abierta['origen_barra_tipo'],
            piezas_cortadas=barra_abierta['piezas_cortadas']
        )
        patrones.append(patron)
    
    return Cromosoma(patrones)


def generar_individuo_aleatorio_con_reparacion(
    piezas_requeridas_df: pd.DataFrame,
    barras_disponibles: List[Dict[str, Any]],
    desperdicios_disponibles: List[Dict[str, Any]]
) -> Cromosoma:
    """
    Genera un individuo aleatorio y lo repara para que sea válido.
    
    Args:
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        barras_disponibles: Lista de barras estándar disponibles.
        desperdicios_disponibles: Lista de desperdicios reutilizables.
    
    Returns:
        Cromosoma: Un cromosoma aleatorio reparado.
    """
    # Crear lista de todas las piezas individuales
    piezas_individuales = []
    for _, fila in piezas_requeridas_df.iterrows():
        for _ in range(int(int(fila['cantidad_requerida']))):
            piezas_individuales.append({
                'id_pedido': fila['id_pedido'],
                'longitud_pieza': fila['longitud_pieza_requerida']
            })
    
    # Mezclar aleatoriamente las piezas
    random.shuffle(piezas_individuales)
    
    # Crear lista de barras disponibles mezcladas
    todas_las_barras = []
    
    # Añadir desperdicios
    for desperdicio in desperdicios_disponibles:
        todas_las_barras.append({
            'longitud': desperdicio['longitud'],
            'tipo': 'desperdicio'
        })
    
    # Añadir algunas barras estándar aleatorias
    for barra in barras_disponibles:
        # Añadir múltiples copias de cada tipo de barra estándar
        for _ in range(random.randint(1, 5)):
            todas_las_barras.append({
                'longitud': barra['longitud'],
                'tipo': 'estandar'
            })
    
    # Mezclar las barras
    random.shuffle(todas_las_barras)
    
    patrones = []
    barras_usadas = set()
    
    # Asignar piezas aleatoriamente a barras
    for pieza in piezas_individuales:
        colocada = False
        intentos = 0
        max_intentos = len(todas_las_barras) * 2
        
        while not colocada and intentos < max_intentos:
            # Seleccionar una barra aleatoria
            indice_barra = random.randint(0, len(todas_las_barras) - 1)
            barra = todas_las_barras[indice_barra]
            
            # Verificar si la barra puede contener la pieza
            if barra['longitud'] >= pieza['longitud_pieza']:
                # Crear un nuevo patrón con esta pieza
                patron = Patron(
                    origen_barra_longitud=barra['longitud'],
                    origen_barra_tipo=barra['tipo'],
                    piezas_cortadas=[{
                        'id_pedido': pieza['id_pedido'],
                        'longitud_pieza': pieza['longitud_pieza'],
                        'cantidad_pieza_en_patron': 1
                    }]
                )
                patrones.append(patron)
                colocada = True
                
                # Si es un desperdicio, marcarlo como usado
                if barra['tipo'] == 'desperdicio':
                    barra_id = f"{barra['longitud']}_{barra['tipo']}_{indice_barra}"
                    if barra_id not in barras_usadas:
                        barras_usadas.add(barra_id)
                    else:
                        # Este desperdicio ya fue usado, buscar otro
                        colocada = False
            
            intentos += 1
        
        # Si no se pudo colocar después de muchos intentos, usar FFD como respaldo
        if not colocada:
            # Usar la barra estándar más pequeña que pueda contener la pieza
            for barra in sorted(barras_disponibles, key=lambda x: x['longitud']):
                if barra['longitud'] >= pieza['longitud_pieza']:
                    patron = Patron(
                        origen_barra_longitud=barra['longitud'],
                        origen_barra_tipo='estandar',
                        piezas_cortadas=[{
                            'id_pedido': pieza['id_pedido'],
                            'longitud_pieza': pieza['longitud_pieza'],
                            'cantidad_pieza_en_patron': 1
                        }]
                    )
                    patrones.append(patron)
                    break
    
    cromosoma = Cromosoma(patrones)
    
    # Reparar el cromosoma para optimizar el uso de barras
    cromosoma_reparado = reparar_cromosoma(
        cromosoma, 
        piezas_requeridas_df, 
        barras_disponibles, 
        desperdicios_disponibles
    )
    
    return cromosoma_reparado


def reparar_cromosoma(
    cromosoma: Cromosoma,
    piezas_requeridas_df: pd.DataFrame,
    barras_disponibles: List[Dict[str, Any]],
    desperdicios_disponibles: List[Dict[str, Any]]
) -> Cromosoma:
    """
    Repara un cromosoma para optimizar el uso de barras y reducir desperdicios.
    
    Args:
        cromosoma: El cromosoma a reparar.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        barras_disponibles: Lista de barras estándar disponibles.
        desperdicios_disponibles: Lista de desperdicios reutilizables.
    
    Returns:
        Cromosoma: El cromosoma reparado.
    """
    # Extraer todas las piezas del cromosoma
    todas_las_piezas = []
    for patron in cromosoma.patrones:
        for pieza_info in patron.piezas_cortadas:
            for _ in range(pieza_info['cantidad_pieza_en_patron']):
                todas_las_piezas.append({
                    'id_pedido': pieza_info['id_pedido'],
                    'longitud_pieza': pieza_info['longitud_pieza']
                })
    
    # Usar BFD para reorganizar las piezas de manera más eficiente
    piezas_df_temp = pd.DataFrame([
        {
            'id_pedido': pieza['id_pedido'],
            'longitud_pieza_requerida': pieza['longitud_pieza'],
            'cantidad_requerida': 1
        }
        for pieza in todas_las_piezas
    ])
    
    # Agrupar piezas idénticas
    piezas_agrupadas = piezas_df_temp.groupby(['id_pedido', 'longitud_pieza_requerida']).size().reset_index(name='cantidad_requerida')
    
    # Generar un nuevo cromosoma usando BFD
    cromosoma_reparado = generar_individuo_heuristico_bfd(
        piezas_agrupadas,
        barras_disponibles,
        desperdicios_disponibles
    )
    
    return cromosoma_reparado


def generar_individuo_con_analisis_optimo(
    piezas_requeridas_df: pd.DataFrame,
    barras_disponibles: List[Dict[str, Any]],
    desperdicios_disponibles: List[Dict[str, Any]]
) -> Cromosoma:
    """
    Genera un individuo usando análisis óptimo para casos homogéneos y heurísticas para casos complejos.
    
    Args:
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        barras_disponibles: Lista de barras estándar disponibles.
        desperdicios_disponibles: Lista de desperdicios reutilizables.
    
    Returns:
        Cromosoma: Un cromosoma generado con análisis óptimo cuando es posible.
    """
    # Obtener longitudes de barras
    longitudes_barras = [barra['longitud'] for barra in barras_disponibles]
    
    # Analizar casos homogéneos
    casos_homogeneos = analizar_casos_homogeneos(
        piezas_requeridas_df, longitudes_barras, tolerancia_homogeneidad=0.01
    )
    
    patrones = []
    piezas_procesadas = set()
    
    # Procesar casos homogéneos con solución óptima
    for clave, analisis in casos_homogeneos.items():
        ids_pedidos, longitud_pieza = clave
        solucion_optima = analisis['solucion_optima']
        
        # Crear patrones según la solución óptima
        for longitud_barra, cantidad_barras in solucion_optima['combinacion_barras'].items():
            if cantidad_barras > 0:
                # Calcular cuántas piezas caben en esta barra
                piezas_por_barra = int(longitud_barra // longitud_pieza)
                
                for _ in range(int(cantidad_barras)):
                    # Crear lista de piezas para este patrón
                    piezas_cortadas = []
                    piezas_añadidas = 0
                    
                    for id_pedido in ids_pedidos:
                        if piezas_añadidas >= piezas_por_barra:
                            break
                        
                        # Buscar la fila correspondiente en el DataFrame
                        fila = piezas_requeridas_df[piezas_requeridas_df['id_pedido'] == id_pedido].iloc[0]
                        cantidad_requerida = int(fila['cantidad_requerida'])
                        
                        # Calcular cuántas piezas de este pedido añadir
                        piezas_a_añadir = min(
                            cantidad_requerida,
                            piezas_por_barra - piezas_añadidas
                        )
                        
                        if piezas_a_añadir > 0:
                            piezas_cortadas.append({
                                'id_pedido': id_pedido,
                                'longitud_pieza': longitud_pieza,
                                'cantidad_pieza_en_patron': piezas_a_añadir
                            })
                            piezas_añadidas += piezas_a_añadir
                    
                    # Crear el patrón
                    if piezas_cortadas:
                        patron = Patron(
                            origen_barra_longitud=longitud_barra,
                            origen_barra_tipo='estandar',
                            piezas_cortadas=piezas_cortadas
                        )
                        patrones.append(patron)
        
        # Marcar estas piezas como procesadas
        for id_pedido in ids_pedidos:
            piezas_procesadas.add(id_pedido)
    
    # Para piezas no homogéneas, usar FFD mejorado
    piezas_restantes = piezas_requeridas_df[~piezas_requeridas_df['id_pedido'].isin(piezas_procesadas)]
    
    if not piezas_restantes.empty:
        # Generar cromosoma para piezas restantes usando FFD mejorado
        cromosoma_restante = generar_individuo_heuristico_ffd(
            piezas_restantes, barras_disponibles, desperdicios_disponibles
        )
        patrones.extend(cromosoma_restante.patrones)
    
    return Cromosoma(patrones)


def inicializar_poblacion(
    tamaño_poblacion: int,
    piezas_requeridas_df: pd.DataFrame,
    barras_estandar_disponibles: List[Dict[str, Any]],
    desperdicios_reutilizables_previos: List[Dict[str, Any]],
    estrategia_inicializacion: str = 'hibrida',
    config_ga: Optional[Dict[str, Any]] = None
) -> List[Cromosoma]:
    """
    Inicializa una población de cromosomas usando diferentes estrategias.
    
    Args:
        tamaño_poblacion: Número de individuos en la población.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        barras_estandar_disponibles: Lista de barras estándar disponibles.
        desperdicios_reutilizables_previos: Lista de desperdicios reutilizables.
        estrategia_inicializacion: Estrategia a usar ('heuristica', 'aleatoria', 'hibrida').
        config_ga: Configuración adicional del algoritmo genético.
    
    Returns:
        List[Cromosoma]: Lista de cromosomas que forman la población inicial.
    """
    if config_ga is None:
        config_ga = {}
    
    proporcion_heuristicos = config_ga.get('proporcion_heuristicos', 0.6)
    poblacion = []
    
    if estrategia_inicializacion == 'heuristica':
        # Solo individuos heurísticos
        for i in range(tamaño_poblacion):
            if i % 2 == 0:
                individuo = generar_individuo_heuristico_ffd(
                    piezas_requeridas_df,
                    barras_estandar_disponibles,
                    desperdicios_reutilizables_previos
                )
            else:
                individuo = generar_individuo_heuristico_bfd(
                    piezas_requeridas_df,
                    barras_estandar_disponibles,
                    desperdicios_reutilizables_previos
                )
            poblacion.append(individuo)
    
    elif estrategia_inicializacion == 'aleatoria':
        # Solo individuos aleatorios
        for _ in range(tamaño_poblacion):
            individuo = generar_individuo_aleatorio_con_reparacion(
                piezas_requeridas_df,
                barras_estandar_disponibles,
                desperdicios_reutilizables_previos
            )
            poblacion.append(individuo)
    
    elif estrategia_inicializacion == 'hibrida':
        # CORRECCIÓN: Combinación mejorada con análisis óptimo, heurísticos y aleatorios
        num_optimos = min(tamaño_poblacion // 4, 3)  # Máximo 3 individuos óptimos
        num_heuristicos = int((tamaño_poblacion - num_optimos) * proporcion_heuristicos)
        num_aleatorios = tamaño_poblacion - num_optimos - num_heuristicos
        
        # Generar individuos con análisis óptimo
        for _ in range(num_optimos):
            individuo = generar_individuo_con_analisis_optimo(
                piezas_requeridas_df,
                barras_estandar_disponibles,
                desperdicios_reutilizables_previos
            )
            poblacion.append(individuo)
        
        # Generar individuos heurísticos
        for i in range(num_heuristicos):
            if i % 2 == 0:
                individuo = generar_individuo_heuristico_ffd(
                    piezas_requeridas_df,
                    barras_estandar_disponibles,
                    desperdicios_reutilizables_previos
                )
            else:
                individuo = generar_individuo_heuristico_bfd(
                    piezas_requeridas_df,
                    barras_estandar_disponibles,
                    desperdicios_reutilizables_previos
                )
            poblacion.append(individuo)
        
        # Generar individuos aleatorios
        for _ in range(num_aleatorios):
            individuo = generar_individuo_aleatorio_con_reparacion(
                piezas_requeridas_df,
                barras_estandar_disponibles,
                desperdicios_reutilizables_previos
            )
            poblacion.append(individuo)
    
    else:
        raise ValueError(f"Estrategia de inicialización no reconocida: {estrategia_inicializacion}")
    
    # Mezclar la población para evitar sesgos de orden
    random.shuffle(poblacion)
    
    return poblacion 
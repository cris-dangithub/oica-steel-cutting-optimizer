"""
Módulo para el operador de cruce en el algoritmo genético.

Este módulo implementa diferentes estrategias de cruce para combinar
cromosomas padres y generar descendencia.
"""

import random
import copy
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from .chromosome import Cromosoma, Patron
from .chromosome_utils import calcular_sumario_piezas_en_cromosoma
from .population import reparar_cromosoma


def cruce_un_punto(
    padre1: Cromosoma,
    padre2: Cromosoma,
    piezas_requeridas_df: pd.DataFrame
) -> Tuple[Cromosoma, Cromosoma]:
    """
    Realiza cruce de un punto entre dos cromosomas padres.
    
    Args:
        padre1: Primer cromosoma padre.
        padre2: Segundo cromosoma padre.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
    
    Returns:
        Tuple[Cromosoma, Cromosoma]: Dos cromosomas hijos resultantes del cruce.
    """
    # Si algún padre está vacío, retornar copias de los padres
    if len(padre1.patrones) == 0 or len(padre2.patrones) == 0:
        return copy.deepcopy(padre1), copy.deepcopy(padre2)
    
    # Determinar punto de cruce para cada padre
    punto_cruce_1 = random.randint(1, len(padre1.patrones))
    punto_cruce_2 = random.randint(1, len(padre2.patrones))
    
    # Crear hijos combinando segmentos de los padres
    patrones_hijo1 = (
        padre1.patrones[:punto_cruce_1] + 
        padre2.patrones[punto_cruce_2:]
    )
    
    patrones_hijo2 = (
        padre2.patrones[:punto_cruce_2] + 
        padre1.patrones[punto_cruce_1:]
    )
    
    # Crear cromosomas hijos
    hijo1 = Cromosoma(copy.deepcopy(patrones_hijo1))
    hijo2 = Cromosoma(copy.deepcopy(patrones_hijo2))
    
    return hijo1, hijo2


def cruce_dos_puntos(
    padre1: Cromosoma,
    padre2: Cromosoma,
    piezas_requeridas_df: pd.DataFrame
) -> Tuple[Cromosoma, Cromosoma]:
    """
    Realiza cruce de dos puntos entre dos cromosomas padres.
    
    Args:
        padre1: Primer cromosoma padre.
        padre2: Segundo cromosoma padre.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
    
    Returns:
        Tuple[Cromosoma, Cromosoma]: Dos cromosomas hijos resultantes del cruce.
    """
    # Si algún padre está vacío, retornar copias de los padres
    if len(padre1.patrones) == 0 or len(padre2.patrones) == 0:
        return copy.deepcopy(padre1), copy.deepcopy(padre2)
    
    # Determinar puntos de cruce para cada padre
    len1, len2 = len(padre1.patrones), len(padre2.patrones)
    
    # Para padre1
    if len1 > 1:
        punto1_1 = random.randint(0, len1 - 1)
        punto2_1 = random.randint(punto1_1 + 1, len1)
    else:
        punto1_1, punto2_1 = 0, 1
    
    # Para padre2
    if len2 > 1:
        punto1_2 = random.randint(0, len2 - 1)
        punto2_2 = random.randint(punto1_2 + 1, len2)
    else:
        punto1_2, punto2_2 = 0, 1
    
    # Crear hijos intercambiando segmentos centrales
    patrones_hijo1 = (
        padre1.patrones[:punto1_1] + 
        padre2.patrones[punto1_2:punto2_2] + 
        padre1.patrones[punto2_1:]
    )
    
    patrones_hijo2 = (
        padre2.patrones[:punto1_2] + 
        padre1.patrones[punto1_1:punto2_1] + 
        padre2.patrones[punto2_2:]
    )
    
    # Crear cromosomas hijos
    hijo1 = Cromosoma(copy.deepcopy(patrones_hijo1))
    hijo2 = Cromosoma(copy.deepcopy(patrones_hijo2))
    
    return hijo1, hijo2


def cruce_basado_en_piezas(
    padre1: Cromosoma,
    padre2: Cromosoma,
    piezas_requeridas_df: pd.DataFrame
) -> Tuple[Cromosoma, Cromosoma]:
    """
    Realiza cruce basado en las piezas satisfechas por cada patrón.
    
    Este método más sofisticado intenta preservar patrones que satisfacen
    piezas específicas de manera eficiente.
    
    Args:
        padre1: Primer cromosoma padre.
        padre2: Segundo cromosoma padre.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
    
    Returns:
        Tuple[Cromosoma, Cromosoma]: Dos cromosomas hijos resultantes del cruce.
    """
    # Crear diccionario de piezas requeridas para referencia rápida
    piezas_requeridas = {}
    for _, fila in piezas_requeridas_df.iterrows():
        clave = (fila['id_pedido'], fila['longitud_pieza_requerida'])
        piezas_requeridas[clave] = fila['cantidad_requerida']
    
    # Analizar qué piezas satisface cada patrón en cada padre
    def analizar_patrones(cromosoma):
        patrones_info = []
        for i, patron in enumerate(cromosoma.patrones):
            piezas_en_patron = set()
            for pieza_info in patron.piezas_cortadas:
                clave = (pieza_info['id_pedido'], pieza_info['longitud_pieza'])
                piezas_en_patron.add(clave)
            
            patrones_info.append({
                'indice': i,
                'patron': patron,
                'piezas': piezas_en_patron,
                'eficiencia': 1.0 - (patron.desperdicio_patron_longitud / patron.origen_barra_longitud)
            })
        return patrones_info
    
    info_padre1 = analizar_patrones(padre1)
    info_padre2 = analizar_patrones(padre2)
    
    # Seleccionar patrones para cada hijo basándose en eficiencia y diversidad
    def seleccionar_patrones_para_hijo(info_p1, info_p2, preferir_p1=True):
        patrones_seleccionados = []
        piezas_cubiertas = set()
        
        # Combinar y ordenar patrones por eficiencia
        todos_patrones = []
        for info in info_p1:
            todos_patrones.append(('p1', info))
        for info in info_p2:
            todos_patrones.append(('p2', info))
        
        # Ordenar por eficiencia descendente
        todos_patrones.sort(key=lambda x: x[1]['eficiencia'], reverse=True)
        
        # Seleccionar patrones evitando redundancia excesiva
        for origen, info in todos_patrones:
            # Verificar si este patrón aporta piezas nuevas o mejora la eficiencia
            piezas_nuevas = info['piezas'] - piezas_cubiertas
            
            if piezas_nuevas or len(patrones_seleccionados) < 2:
                # Añadir el patrón
                patrones_seleccionados.append(copy.deepcopy(info['patron']))
                piezas_cubiertas.update(info['piezas'])
                
                # Limitar el número de patrones para evitar cromosomas muy grandes
                if len(patrones_seleccionados) >= max(len(info_p1), len(info_p2)) + 2:
                    break
        
        return patrones_seleccionados
    
    # Crear los hijos
    patrones_hijo1 = seleccionar_patrones_para_hijo(info_padre1, info_padre2, True)
    patrones_hijo2 = seleccionar_patrones_para_hijo(info_padre2, info_padre1, False)
    
    hijo1 = Cromosoma(patrones_hijo1)
    hijo2 = Cromosoma(patrones_hijo2)
    
    return hijo1, hijo2


def reparar_descendencia(
    hijo: Cromosoma,
    piezas_requeridas_df: pd.DataFrame,
    barras_disponibles: List[Dict[str, Any]],
    desperdicios_disponibles: List[Dict[str, Any]]
) -> Cromosoma:
    """
    Repara un cromosoma hijo para asegurar que sea válido y eficiente.
    
    Args:
        hijo: Cromosoma hijo a reparar.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        barras_disponibles: Lista de barras estándar disponibles.
        desperdicios_disponibles: Lista de desperdicios reutilizables.
    
    Returns:
        Cromosoma: Cromosoma hijo reparado.
    """
    # Usar la función de reparación del módulo de población
    return reparar_cromosoma(
        hijo,
        piezas_requeridas_df,
        barras_disponibles,
        desperdicios_disponibles
    )


def validar_descendencia(
    hijo: Cromosoma,
    piezas_requeridas_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Valida si un cromosoma hijo cumple con los requisitos básicos.
    
    Args:
        hijo: Cromosoma hijo a validar.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
    
    Returns:
        Dict[str, Any]: Información sobre la validez del cromosoma.
    """
    # Calcular sumario de piezas en el cromosoma
    sumario_piezas = calcular_sumario_piezas_en_cromosoma(hijo)
    
    # Crear diccionario de piezas requeridas
    piezas_requeridas = {}
    for _, fila in piezas_requeridas_df.iterrows():
        clave = (fila['id_pedido'], fila['longitud_pieza_requerida'])
        piezas_requeridas[clave] = fila['cantidad_requerida']
    
    # Verificar cobertura
    faltantes = {}
    sobrantes = {}
    
    # Verificar faltantes
    for clave, cantidad_requerida in piezas_requeridas.items():
        cantidad_en_cromosoma = sumario_piezas.get(clave, 0)
        if cantidad_en_cromosoma < cantidad_requerida:
            faltantes[clave] = cantidad_requerida - cantidad_en_cromosoma
    
    # Verificar sobrantes
    for clave, cantidad_en_cromosoma in sumario_piezas.items():
        cantidad_requerida = piezas_requeridas.get(clave, 0)
        if cantidad_en_cromosoma > cantidad_requerida:
            sobrantes[clave] = cantidad_en_cromosoma - cantidad_requerida
    
    return {
        'es_valido': len(faltantes) == 0,
        'faltantes': faltantes,
        'sobrantes': sobrantes,
        'desperdicio_total': hijo.calcular_desperdicio_total(),
        'num_patrones': len(hijo.patrones)
    }


def cruzar(
    padre1_cromosoma: Cromosoma,
    padre2_cromosoma: Cromosoma,
    piezas_requeridas_df: pd.DataFrame,
    tasa_cruce: float,
    estrategia_cruce: str,
    config_ga: Optional[Dict[str, Any]] = None
) -> Tuple[Cromosoma, Cromosoma]:
    """
    Realiza el cruce entre dos cromosomas padres.
    
    Args:
        padre1_cromosoma: Primer cromosoma padre.
        padre2_cromosoma: Segundo cromosoma padre.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        tasa_cruce: Probabilidad de que ocurra el cruce (0.0 a 1.0).
        estrategia_cruce: Estrategia de cruce ('un_punto', 'dos_puntos', 'basado_en_piezas').
        config_ga: Configuración adicional del algoritmo genético.
    
    Returns:
        Tuple[Cromosoma, Cromosoma]: Dos cromosomas hijos resultantes.
    """
    if config_ga is None:
        config_ga = {}
    
    # Decidir si realizar el cruce basándose en la tasa de cruce
    if random.random() > tasa_cruce:
        # No realizar cruce, retornar copias de los padres
        return copy.deepcopy(padre1_cromosoma), copy.deepcopy(padre2_cromosoma)
    
    # Realizar el cruce según la estrategia especificada
    if estrategia_cruce == 'un_punto':
        hijo1, hijo2 = cruce_un_punto(padre1_cromosoma, padre2_cromosoma, piezas_requeridas_df)
    elif estrategia_cruce == 'dos_puntos':
        hijo1, hijo2 = cruce_dos_puntos(padre1_cromosoma, padre2_cromosoma, piezas_requeridas_df)
    elif estrategia_cruce == 'basado_en_piezas':
        hijo1, hijo2 = cruce_basado_en_piezas(padre1_cromosoma, padre2_cromosoma, piezas_requeridas_df)
    else:
        raise ValueError(f"Estrategia de cruce no reconocida: {estrategia_cruce}")
    
    # Reparar los hijos si es necesario
    reparar_hijos = config_ga.get('reparar_hijos_cruce', True)
    if reparar_hijos:
        barras_disponibles = config_ga.get('barras_disponibles', [])
        desperdicios_disponibles = config_ga.get('desperdicios_disponibles', [])
        
        if barras_disponibles:  # Solo reparar si tenemos información de barras
            hijo1 = reparar_descendencia(hijo1, piezas_requeridas_df, barras_disponibles, desperdicios_disponibles)
            hijo2 = reparar_descendencia(hijo2, piezas_requeridas_df, barras_disponibles, desperdicios_disponibles)
    
    return hijo1, hijo2


def cruce_poblacion(
    parejas: List[Tuple[Cromosoma, Cromosoma]],
    piezas_requeridas_df: pd.DataFrame,
    tasa_cruce: float,
    estrategia_cruce: str,
    config_ga: Optional[Dict[str, Any]] = None
) -> List[Cromosoma]:
    """
    Realiza el cruce para una lista de parejas de padres.
    
    Args:
        parejas: Lista de parejas de cromosomas padres.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        tasa_cruce: Probabilidad de que ocurra el cruce.
        estrategia_cruce: Estrategia de cruce a utilizar.
        config_ga: Configuración adicional del algoritmo genético.
    
    Returns:
        List[Cromosoma]: Lista de cromosomas hijos resultantes.
    """
    hijos = []
    
    for padre1, padre2 in parejas:
        hijo1, hijo2 = cruzar(
            padre1,
            padre2,
            piezas_requeridas_df,
            tasa_cruce,
            estrategia_cruce,
            config_ga
        )
        hijos.extend([hijo1, hijo2])
    
    return hijos


def analizar_diversidad_cruce(
    padres: List[Cromosoma],
    hijos: List[Cromosoma]
) -> Dict[str, float]:
    """
    Analiza la diversidad introducida por el operador de cruce.
    
    Args:
        padres: Lista de cromosomas padres.
        hijos: Lista de cromosomas hijos.
    
    Returns:
        Dict[str, float]: Métricas de diversidad.
    """
    def calcular_diversidad_promedio(cromosomas):
        if len(cromosomas) < 2:
            return 0.0
        
        diversidad_total = 0.0
        comparaciones = 0
        
        for i in range(len(cromosomas)):
            for j in range(i + 1, len(cromosomas)):
                # Calcular diferencia entre cromosomas
                # (simplificado: diferencia en número de patrones y desperdicio)
                diff_patrones = abs(len(cromosomas[i].patrones) - len(cromosomas[j].patrones))
                diff_desperdicio = abs(
                    cromosomas[i].calcular_desperdicio_total() - 
                    cromosomas[j].calcular_desperdicio_total()
                )
                
                diversidad = diff_patrones + diff_desperdicio
                diversidad_total += diversidad
                comparaciones += 1
        
        return diversidad_total / comparaciones if comparaciones > 0 else 0.0
    
    diversidad_padres = calcular_diversidad_promedio(padres)
    diversidad_hijos = calcular_diversidad_promedio(hijos)
    
    return {
        'diversidad_padres': diversidad_padres,
        'diversidad_hijos': diversidad_hijos,
        'incremento_diversidad': diversidad_hijos - diversidad_padres,
        'ratio_diversidad': diversidad_hijos / diversidad_padres if diversidad_padres > 0 else 0.0
    } 
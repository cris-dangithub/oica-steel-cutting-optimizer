"""
Módulo para el operador de mutación en el algoritmo genético.

Este módulo implementa diferentes operaciones de mutación para introducir
variaciones aleatorias en los cromosomas y mantener la diversidad genética.
"""

import random
import copy
from typing import List, Dict, Any, Optional
import pandas as pd

from .chromosome import Cromosoma, Patron
from .chromosome_utils import calcular_sumario_piezas_en_cromosoma
from .population import generar_individuo_heuristico_bfd


def mutacion_cambiar_origen_patron(
    cromosoma: Cromosoma,
    indice_patron: int,
    nuevas_barras_disponibles: List[Dict[str, Any]]
) -> bool:
    """
    Cambia la barra origen de un patrón específico.
    
    Args:
        cromosoma: Cromosoma a mutar.
        indice_patron: Índice del patrón a modificar.
        nuevas_barras_disponibles: Lista de barras disponibles para el cambio.
    
    Returns:
        bool: True si la mutación fue exitosa, False en caso contrario.
    """
    if indice_patron >= len(cromosoma.patrones) or not nuevas_barras_disponibles:
        return False
    
    patron = cromosoma.patrones[indice_patron]
    
    # Calcular la longitud mínima necesaria para las piezas del patrón
    longitud_necesaria = sum(
        pieza_info['longitud_pieza'] * pieza_info['cantidad_pieza_en_patron']
        for pieza_info in patron.piezas_cortadas
    )
    
    # Buscar barras que puedan contener las piezas
    barras_validas = [
        barra for barra in nuevas_barras_disponibles
        if barra['longitud'] >= longitud_necesaria
    ]
    
    if not barras_validas:
        return False
    
    # Seleccionar una nueva barra aleatoriamente
    nueva_barra = random.choice(barras_validas)
    
    # Actualizar el patrón
    patron.origen_barra_longitud = nueva_barra['longitud']
    patron.origen_barra_tipo = nueva_barra.get('tipo', 'estandar')
    patron._calcular_desperdicio()
    
    return True


def mutacion_reoptimizar_patron(
    cromosoma: Cromosoma,
    indice_patron: int,
    piezas_objetivo: List[Dict[str, Any]],
    barras_disponibles: List[Dict[str, Any]]
) -> bool:
    """
    Re-optimiza un patrón usando un algoritmo heurístico.
    
    Args:
        cromosoma: Cromosoma a mutar.
        indice_patron: Índice del patrón a re-optimizar.
        piezas_objetivo: Lista de piezas que debe contener el patrón.
        barras_disponibles: Lista de barras disponibles.
    
    Returns:
        bool: True si la mutación fue exitosa, False en caso contrario.
    """
    if indice_patron >= len(cromosoma.patrones) or not piezas_objetivo:
        return False
    
    # Crear DataFrame temporal con las piezas objetivo
    piezas_df = pd.DataFrame([
        {
            'id_pedido': pieza['id_pedido'],
            'longitud_pieza_requerida': pieza['longitud_pieza'],
            'cantidad_requerida': pieza.get('cantidad', 1)
        }
        for pieza in piezas_objetivo
    ])
    
    # Generar un nuevo cromosoma optimizado para estas piezas
    cromosoma_temp = generar_individuo_heuristico_bfd(piezas_df, barras_disponibles, [])
    
    if len(cromosoma_temp.patrones) > 0:
        # Reemplazar el patrón original con el primer patrón optimizado
        cromosoma.patrones[indice_patron] = cromosoma_temp.patrones[0]
        return True
    
    return False


def mutacion_mover_pieza(
    cromosoma: Cromosoma,
    patron_origen: int,
    patron_destino: int,
    pieza_info: Dict[str, Any]
) -> bool:
    """
    Mueve una pieza de un patrón a otro.
    
    Args:
        cromosoma: Cromosoma a mutar.
        patron_origen: Índice del patrón origen.
        patron_destino: Índice del patrón destino.
        pieza_info: Información de la pieza a mover.
    
    Returns:
        bool: True si la mutación fue exitosa, False en caso contrario.
    """
    if (patron_origen >= len(cromosoma.patrones) or 
        patron_destino >= len(cromosoma.patrones) or
        patron_origen == patron_destino):
        return False
    
    patron_orig = cromosoma.patrones[patron_origen]
    patron_dest = cromosoma.patrones[patron_destino]
    
    # Buscar la pieza en el patrón origen
    pieza_encontrada = None
    for i, pieza in enumerate(patron_orig.piezas_cortadas):
        if (pieza['id_pedido'] == pieza_info['id_pedido'] and
            pieza['longitud_pieza'] == pieza_info['longitud_pieza']):
            pieza_encontrada = i
            break
    
    if pieza_encontrada is None:
        return False
    
    # Verificar si el patrón destino puede acomodar la pieza
    longitud_pieza = pieza_info['longitud_pieza']
    espacio_disponible = (patron_dest.origen_barra_longitud - 
                         sum(p['longitud_pieza'] * p['cantidad_pieza_en_patron'] 
                             for p in patron_dest.piezas_cortadas))
    
    if espacio_disponible < longitud_pieza:
        return False
    
    # Realizar el movimiento
    pieza_a_mover = patron_orig.piezas_cortadas[pieza_encontrada]
    
    # Reducir cantidad en el patrón origen
    if pieza_a_mover['cantidad_pieza_en_patron'] > 1:
        pieza_a_mover['cantidad_pieza_en_patron'] -= 1
    else:
        # Eliminar la pieza completamente
        patron_orig.piezas_cortadas.pop(pieza_encontrada)
    
    # Añadir la pieza al patrón destino
    pieza_existente = None
    for pieza in patron_dest.piezas_cortadas:
        if (pieza['id_pedido'] == pieza_info['id_pedido'] and
            pieza['longitud_pieza'] == pieza_info['longitud_pieza']):
            pieza_existente = pieza
            break
    
    if pieza_existente:
        pieza_existente['cantidad_pieza_en_patron'] += 1
    else:
        patron_dest.piezas_cortadas.append({
            'id_pedido': pieza_info['id_pedido'],
            'longitud_pieza': pieza_info['longitud_pieza'],
            'cantidad_pieza_en_patron': 1
        })
    
    # Recalcular desperdicios
    patron_orig._calcular_desperdicio()
    patron_dest._calcular_desperdicio()
    
    return True


def mutacion_ajustar_cantidad_piezas(
    cromosoma: Cromosoma,
    piezas_requeridas_df: pd.DataFrame
) -> bool:
    """
    Ajusta las cantidades de piezas para equilibrar la demanda.
    
    Args:
        cromosoma: Cromosoma a mutar.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
    
    Returns:
        bool: True si la mutación fue exitosa, False en caso contrario.
    """
    # Calcular sumario actual
    sumario_actual = calcular_sumario_piezas_en_cromosoma(cromosoma)
    
    # Crear diccionario de piezas requeridas
    piezas_requeridas = {}
    for _, fila in piezas_requeridas_df.iterrows():
        clave = (fila['id_pedido'], fila['longitud_pieza_requerida'])
        piezas_requeridas[clave] = fila['cantidad_requerida']
    
    # Identificar desbalances
    faltantes = []
    sobrantes = []
    
    for clave, cantidad_requerida in piezas_requeridas.items():
        cantidad_actual = sumario_actual.get(clave, 0)
        if cantidad_actual < cantidad_requerida:
            faltantes.append((clave, cantidad_requerida - cantidad_actual))
        elif cantidad_actual > cantidad_requerida:
            sobrantes.append((clave, cantidad_actual - cantidad_requerida))
    
    if not faltantes and not sobrantes:
        return False  # No hay desbalances que corregir
    
    # Intentar corregir un desbalance aleatorio
    if faltantes and random.random() < 0.7:  # Priorizar corregir faltantes
        # Añadir una pieza faltante a un patrón con espacio
        clave_faltante, _ = random.choice(faltantes)
        id_pedido, longitud_pieza = clave_faltante
        
        for patron in cromosoma.patrones:
            espacio_disponible = (patron.origen_barra_longitud - 
                                sum(p['longitud_pieza'] * p['cantidad_pieza_en_patron'] 
                                    for p in patron.piezas_cortadas))
            
            if espacio_disponible >= longitud_pieza:
                # Añadir la pieza
                pieza_existente = None
                for pieza in patron.piezas_cortadas:
                    if (pieza['id_pedido'] == id_pedido and
                        pieza['longitud_pieza'] == longitud_pieza):
                        pieza_existente = pieza
                        break
                
                if pieza_existente:
                    pieza_existente['cantidad_pieza_en_patron'] += 1
                else:
                    patron.piezas_cortadas.append({
                        'id_pedido': id_pedido,
                        'longitud_pieza': longitud_pieza,
                        'cantidad_pieza_en_patron': 1
                    })
                
                patron._calcular_desperdicio()
                return True
    
    elif sobrantes:
        # Eliminar una pieza sobrante
        clave_sobrante, _ = random.choice(sobrantes)
        id_pedido, longitud_pieza = clave_sobrante
        
        for patron in cromosoma.patrones:
            for i, pieza in enumerate(patron.piezas_cortadas):
                if (pieza['id_pedido'] == id_pedido and
                    pieza['longitud_pieza'] == longitud_pieza):
                    
                    if pieza['cantidad_pieza_en_patron'] > 1:
                        pieza['cantidad_pieza_en_patron'] -= 1
                    else:
                        patron.piezas_cortadas.pop(i)
                    
                    patron._calcular_desperdicio()
                    return True
    
    return False


def mutacion_dividir_patron(
    cromosoma: Cromosoma,
    indice_patron: int,
    barras_disponibles: List[Dict[str, Any]]
) -> bool:
    """
    Divide un patrón en dos patrones más pequeños.
    
    Args:
        cromosoma: Cromosoma a mutar.
        indice_patron: Índice del patrón a dividir.
        barras_disponibles: Lista de barras disponibles.
    
    Returns:
        bool: True si la mutación fue exitosa, False en caso contrario.
    """
    if indice_patron >= len(cromosoma.patrones):
        return False
    
    patron = cromosoma.patrones[indice_patron]
    
    if len(patron.piezas_cortadas) < 2:
        return False  # No se puede dividir un patrón con menos de 2 tipos de piezas
    
    # Dividir las piezas aleatoriamente en dos grupos
    piezas = patron.piezas_cortadas.copy()
    random.shuffle(piezas)
    
    punto_division = random.randint(1, len(piezas) - 1)
    grupo1 = piezas[:punto_division]
    grupo2 = piezas[punto_division:]
    
    # Calcular longitudes necesarias para cada grupo
    longitud_grupo1 = sum(p['longitud_pieza'] * p['cantidad_pieza_en_patron'] for p in grupo1)
    longitud_grupo2 = sum(p['longitud_pieza'] * p['cantidad_pieza_en_patron'] for p in grupo2)
    
    # Buscar barras adecuadas para cada grupo
    barras_grupo1 = [b for b in barras_disponibles if b['longitud'] >= longitud_grupo1]
    barras_grupo2 = [b for b in barras_disponibles if b['longitud'] >= longitud_grupo2]
    
    if not barras_grupo1 or not barras_grupo2:
        return False
    
    # Crear los nuevos patrones
    barra1 = random.choice(barras_grupo1)
    barra2 = random.choice(barras_grupo2)
    
    patron1 = Patron(
        origen_barra_longitud=barra1['longitud'],
        origen_barra_tipo=barra1.get('tipo', 'estandar'),
        piezas_cortadas=copy.deepcopy(grupo1)
    )
    
    patron2 = Patron(
        origen_barra_longitud=barra2['longitud'],
        origen_barra_tipo=barra2.get('tipo', 'estandar'),
        piezas_cortadas=copy.deepcopy(grupo2)
    )
    
    # Reemplazar el patrón original con los dos nuevos
    cromosoma.patrones[indice_patron] = patron1
    cromosoma.patrones.insert(indice_patron + 1, patron2)
    
    return True


def mutacion_combinar_patrones(
    cromosoma: Cromosoma,
    indice1: int,
    indice2: int,
    barras_disponibles: List[Dict[str, Any]]
) -> bool:
    """
    Combina dos patrones en uno solo.
    
    Args:
        cromosoma: Cromosoma a mutar.
        indice1: Índice del primer patrón.
        indice2: Índice del segundo patrón.
        barras_disponibles: Lista de barras disponibles.
    
    Returns:
        bool: True si la mutación fue exitosa, False en caso contrario.
    """
    if (indice1 >= len(cromosoma.patrones) or 
        indice2 >= len(cromosoma.patrones) or
        indice1 == indice2):
        return False
    
    patron1 = cromosoma.patrones[indice1]
    patron2 = cromosoma.patrones[indice2]
    
    # Combinar todas las piezas
    todas_las_piezas = []
    
    # Añadir piezas del primer patrón
    for pieza in patron1.piezas_cortadas:
        todas_las_piezas.append(copy.deepcopy(pieza))
    
    # Añadir piezas del segundo patrón, combinando si son iguales
    for pieza2 in patron2.piezas_cortadas:
        pieza_existente = None
        for pieza in todas_las_piezas:
            if (pieza['id_pedido'] == pieza2['id_pedido'] and
                pieza['longitud_pieza'] == pieza2['longitud_pieza']):
                pieza_existente = pieza
                break
        
        if pieza_existente:
            pieza_existente['cantidad_pieza_en_patron'] += pieza2['cantidad_pieza_en_patron']
        else:
            todas_las_piezas.append(copy.deepcopy(pieza2))
    
    # Calcular longitud total necesaria
    longitud_total = sum(p['longitud_pieza'] * p['cantidad_pieza_en_patron'] for p in todas_las_piezas)
    
    # Buscar una barra que pueda contener todas las piezas
    barras_validas = [b for b in barras_disponibles if b['longitud'] >= longitud_total]
    
    if not barras_validas:
        return False
    
    # Crear el patrón combinado
    barra_seleccionada = random.choice(barras_validas)
    patron_combinado = Patron(
        origen_barra_longitud=barra_seleccionada['longitud'],
        origen_barra_tipo=barra_seleccionada.get('tipo', 'estandar'),
        piezas_cortadas=todas_las_piezas
    )
    
    # Reemplazar los patrones originales
    # Eliminar el patrón con índice mayor primero para no afectar los índices
    if indice1 > indice2:
        cromosoma.patrones.pop(indice1)
        cromosoma.patrones[indice2] = patron_combinado
    else:
        cromosoma.patrones.pop(indice2)
        cromosoma.patrones[indice1] = patron_combinado
    
    return True


def mutar(
    cromosoma: Cromosoma,
    piezas_requeridas_df: pd.DataFrame,
    barras_estandar_disponibles: List[Dict[str, Any]],
    desperdicios_reutilizables_previos: List[Dict[str, Any]],
    tasa_mutacion_individuo: float,
    tasa_mutacion_gen: float,
    config_ga: Optional[Dict[str, Any]] = None
) -> Cromosoma:
    """
    Aplica mutación a un cromosoma.
    
    Args:
        cromosoma: Cromosoma a mutar.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        barras_estandar_disponibles: Lista de barras estándar disponibles.
        desperdicios_reutilizables_previos: Lista de desperdicios reutilizables.
        tasa_mutacion_individuo: Probabilidad de que el individuo sea mutado.
        tasa_mutacion_gen: Probabilidad de que cada gen (patrón) sea mutado.
        config_ga: Configuración adicional del algoritmo genético.
    
    Returns:
        Cromosoma: Cromosoma mutado (puede ser el mismo si no se aplicó mutación).
    """
    if config_ga is None:
        config_ga = {}
    
    # Decidir si mutar el individuo
    if random.random() > tasa_mutacion_individuo:
        return cromosoma
    
    # Crear una copia del cromosoma para mutar
    cromosoma_mutado = copy.deepcopy(cromosoma)
    
    # Obtener operaciones de mutación habilitadas
    operaciones_mutacion = config_ga.get('operaciones_mutacion', [
        'cambiar_origen', 'reoptimizar', 'mover_pieza'
    ])
    
    # Combinar todas las barras disponibles
    todas_las_barras = []
    todas_las_barras.extend(desperdicios_reutilizables_previos)
    todas_las_barras.extend(barras_estandar_disponibles)
    
    # Aplicar mutaciones a los patrones
    for i in range(len(cromosoma_mutado.patrones)):
        if random.random() <= tasa_mutacion_gen:
            # Seleccionar una operación de mutación aleatoria
            operacion = random.choice(operaciones_mutacion)
            
            if operacion == 'cambiar_origen' and todas_las_barras:
                mutacion_cambiar_origen_patron(cromosoma_mutado, i, todas_las_barras)
            
            elif operacion == 'reoptimizar' and todas_las_barras:
                # Extraer piezas del patrón actual para re-optimizar
                patron_actual = cromosoma_mutado.patrones[i]
                piezas_patron = []
                for pieza_info in patron_actual.piezas_cortadas:
                    for _ in range(int(pieza_info['cantidad_pieza_en_patron'])):
                        piezas_patron.append({
                            'id_pedido': pieza_info['id_pedido'],
                            'longitud_pieza': pieza_info['longitud_pieza']
                        })
                
                mutacion_reoptimizar_patron(cromosoma_mutado, i, piezas_patron, todas_las_barras)
            
            elif operacion == 'mover_pieza' and len(cromosoma_mutado.patrones) > 1:
                # Seleccionar un patrón destino diferente
                patrones_destino = [j for j in range(len(cromosoma_mutado.patrones)) if j != i]
                if patrones_destino:
                    patron_destino = random.choice(patrones_destino)
                    
                    # Seleccionar una pieza aleatoria del patrón origen
                    patron_origen = cromosoma_mutado.patrones[i]
                    if patron_origen.piezas_cortadas:
                        pieza_seleccionada = random.choice(patron_origen.piezas_cortadas)
                        mutacion_mover_pieza(cromosoma_mutado, i, patron_destino, pieza_seleccionada)
    
    # Aplicar mutaciones a nivel de cromosoma
    if 'ajustar_cantidad' in operaciones_mutacion and random.random() < 0.1:
        mutacion_ajustar_cantidad_piezas(cromosoma_mutado, piezas_requeridas_df)
    
    if 'dividir_patron' in operaciones_mutacion and random.random() < 0.05 and todas_las_barras:
        if len(cromosoma_mutado.patrones) > 0:
            indice_patron = random.randint(0, len(cromosoma_mutado.patrones) - 1)
            mutacion_dividir_patron(cromosoma_mutado, indice_patron, todas_las_barras)
    
    if 'combinar_patrones' in operaciones_mutacion and random.random() < 0.05 and todas_las_barras:
        if len(cromosoma_mutado.patrones) > 1:
            indices = random.sample(range(len(cromosoma_mutado.patrones)), 2)
            mutacion_combinar_patrones(cromosoma_mutado, indices[0], indices[1], todas_las_barras)
    
    return cromosoma_mutado


def mutar_poblacion(
    poblacion: List[Cromosoma],
    piezas_requeridas_df: pd.DataFrame,
    barras_estandar_disponibles: List[Dict[str, Any]],
    desperdicios_reutilizables_previos: List[Dict[str, Any]],
    tasa_mutacion_individuo: float,
    tasa_mutacion_gen: float,
    config_ga: Optional[Dict[str, Any]] = None
) -> List[Cromosoma]:
    """
    Aplica mutación a toda una población.
    
    Args:
        poblacion: Lista de cromosomas de la población.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        barras_estandar_disponibles: Lista de barras estándar disponibles.
        desperdicios_reutilizables_previos: Lista de desperdicios reutilizables.
        tasa_mutacion_individuo: Probabilidad de que cada individuo sea mutado.
        tasa_mutacion_gen: Probabilidad de que cada gen sea mutado.
        config_ga: Configuración adicional del algoritmo genético.
    
    Returns:
        List[Cromosoma]: Población mutada.
    """
    poblacion_mutada = []
    
    for cromosoma in poblacion:
        cromosoma_mutado = mutar(
            cromosoma,
            piezas_requeridas_df,
            barras_estandar_disponibles,
            desperdicios_reutilizables_previos,
            tasa_mutacion_individuo,
            tasa_mutacion_gen,
            config_ga
        )
        poblacion_mutada.append(cromosoma_mutado)
    
    return poblacion_mutada 
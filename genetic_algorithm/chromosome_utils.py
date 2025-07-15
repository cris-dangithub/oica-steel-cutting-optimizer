"""
Utilidades para manipular y validar cromosomas.

Este módulo contiene funciones auxiliares para crear, validar, analizar y manipular
cromosomas y patrones de corte.
"""

from typing import List, Dict, Any, Tuple, Union, Set
import pandas as pd
from copy import deepcopy

from .chromosome import Patron, Cromosoma
from . import LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE


def crear_patron_corte(origen_longitud: float, origen_tipo: str, 
                       lista_piezas_a_cortar_en_patron: List[Dict[str, Any]]) -> Patron:
    """
    Crea un patrón de corte a partir de los parámetros especificados.
    
    Args:
        origen_longitud: Longitud de la barra de origen en metros.
        origen_tipo: Tipo de barra ('estandar' o 'desperdicio').
        lista_piezas_a_cortar_en_patron: Lista de piezas a incluir en el patrón.
            Cada pieza es un diccionario con 'id_pedido', 'longitud_pieza' y 'cantidad_pieza_en_patron'.
    
    Returns:
        Patron: Un nuevo objeto Patron con las piezas especificadas.
        
    Raises:
        ValueError: Si las piezas no caben en la barra de origen.
    """
    # Crear una copia de la lista para no modificar la original
    piezas_copia = deepcopy(lista_piezas_a_cortar_en_patron)
    
    # Calcular longitud total requerida por las piezas
    longitud_total_requerida = sum(
        pieza['longitud_pieza'] * pieza['cantidad_pieza_en_patron']
        for pieza in piezas_copia
    )
    
    # Verificar si las piezas caben en la barra
    if longitud_total_requerida > origen_longitud:
        raise ValueError(
            f"Las piezas requieren {longitud_total_requerida}m pero la barra origen solo tiene {origen_longitud}m"
        )
    
    # Crear y retornar el nuevo patrón
    return Patron(origen_longitud, origen_tipo, piezas_copia)


def validar_patron(patron: Patron, longitud_minima_desperdicio: float = LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE) -> bool:
    """
    Verifica que un patrón sea válido.
    
    Un patrón es válido si:
    1. La suma de las longitudes de las piezas no excede la longitud de la barra origen.
    2. El cálculo del desperdicio y su clasificación como utilizable es correcto.
    
    Args:
        patron: El patrón a validar.
        longitud_minima_desperdicio: Longitud mínima para considerar un desperdicio utilizable.
    
    Returns:
        bool: True si el patrón es válido, False en caso contrario.
    """
    # Verificar que la suma de piezas no exceda la longitud de la barra
    longitud_total_piezas = sum(
        pieza['longitud_pieza'] * pieza['cantidad_pieza_en_patron']
        for pieza in patron.piezas_cortadas
    )
    
    if longitud_total_piezas > patron.origen_barra_longitud:
        return False
    
    # Verificar el cálculo correcto del desperdicio
    desperdicio_esperado = round(patron.origen_barra_longitud - longitud_total_piezas, 3)
    if abs(desperdicio_esperado - patron.desperdicio_patron_longitud) > 0.001:  # Tolerancia para errores de punto flotante
        return False
    
    # Verificar la clasificación correcta del desperdicio como utilizable
    es_utilizable_esperado = desperdicio_esperado >= longitud_minima_desperdicio
    if es_utilizable_esperado != patron.es_desperdicio_utilizable:
        return False
    
    return True


def calcular_sumario_piezas_en_cromosoma(cromosoma: Cromosoma) -> Dict[Tuple[Any, float], int]:
    """
    Calcula un resumen de las piezas incluidas en un cromosoma.
    
    Args:
        cromosoma: El cromosoma a analizar.
    
    Returns:
        Dict[Tuple[Any, float], int]: Diccionario donde cada clave es una tupla (id_pedido, longitud_pieza)
            y cada valor es la cantidad total de piezas de ese tipo en el cromosoma.
    """
    sumario: Dict[Tuple[Any, float], int] = {}
    
    for patron in cromosoma.patrones:
        for pieza in patron.piezas_cortadas:
            id_pedido = pieza['id_pedido']
            longitud = pieza['longitud_pieza']
            cantidad = pieza['cantidad_pieza_en_patron']
            
            clave = (id_pedido, longitud)
            if clave in sumario:
                sumario[clave] += cantidad
            else:
                sumario[clave] = cantidad
    
    return sumario


def validar_cromosoma_completitud(cromosoma: Cromosoma, piezas_requeridas_df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    """
    Verifica si un cromosoma satisface exactamente la demanda especificada.
    
    Args:
        cromosoma: El cromosoma a validar.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
            Debe tener columnas 'id_pedido', 'longitud_pieza_requerida' y 'cantidad_requerida'.
    
    Returns:
        Tuple[bool, Dict[str, Any]]: Una tupla con:
            - bool: True si el cromosoma satisface exactamente la demanda, False en caso contrario.
            - Dict[str, Any]: Información adicional sobre la validación:
                - 'faltantes': Diccionario con las piezas faltantes y sus cantidades.
                - 'sobrantes': Diccionario con las piezas sobrantes y sus cantidades.
                - 'completo': Booleano que indica si todas las demandas están satisfechas.
                - 'exceso': Booleano que indica si hay piezas en exceso.
    """
    # Calcular el sumario de piezas en el cromosoma
    sumario_cromosoma = calcular_sumario_piezas_en_cromosoma(cromosoma)
    
    # Inicializar diccionarios para piezas faltantes y sobrantes
    faltantes: Dict[Tuple[Any, float], int] = {}
    sobrantes: Dict[Tuple[Any, float], int] = {}
    
    # Verificar cada pieza requerida
    for _, fila in piezas_requeridas_df.iterrows():
        id_pedido = fila['id_pedido']
        longitud = fila['longitud_pieza_requerida']
        cantidad_requerida = fila['cantidad_requerida']
        
        clave = (id_pedido, longitud)
        cantidad_en_cromosoma = sumario_cromosoma.get(clave, 0)
        
        # Verificar si hay faltantes
        if cantidad_en_cromosoma < cantidad_requerida:
            faltantes[clave] = cantidad_requerida - cantidad_en_cromosoma
        
        # Verificar si hay sobrantes
        elif cantidad_en_cromosoma > cantidad_requerida:
            sobrantes[clave] = cantidad_en_cromosoma - cantidad_requerida
    
    # Verificar si hay piezas en el cromosoma que no estaban en los requerimientos
    claves_requeridas = {(fila['id_pedido'], fila['longitud_pieza_requerida']) 
                         for _, fila in piezas_requeridas_df.iterrows()}
    
    for clave in sumario_cromosoma:
        if clave not in claves_requeridas:
            sobrantes[clave] = sumario_cromosoma[clave]
    
    # Determinar si el cromosoma satisface exactamente la demanda
    es_completo = len(faltantes) == 0
    tiene_exceso = len(sobrantes) > 0
    es_exacto = es_completo and not tiene_exceso
    
    # Preparar información detallada
    info = {
        'faltantes': faltantes,
        'sobrantes': sobrantes,
        'completo': es_completo,
        'exceso': tiene_exceso
    }
    
    return es_exacto, info


def calcular_desperdicio_total_cromosoma(cromosoma: Cromosoma) -> float:
    """
    Calcula el desperdicio total generado por un cromosoma.
    
    Args:
        cromosoma: El cromosoma a evaluar.
    
    Returns:
        float: La suma de los desperdicios de todos los patrones en el cromosoma.
    """
    return cromosoma.calcular_desperdicio_total()


def obtener_nuevos_desperdicios_utilizables_de_cromosoma(
    cromosoma: Cromosoma, 
    longitud_minima_desperdicio: float = LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE
) -> List[float]:
    """
    Obtiene una lista de los desperdicios utilizables generados por un cromosoma.
    
    Args:
        cromosoma: El cromosoma a evaluar.
        longitud_minima_desperdicio: Longitud mínima para considerar un desperdicio utilizable.
    
    Returns:
        List[float]: Lista de longitudes de desperdicios utilizables.
    """
    return cromosoma.obtener_desperdicios_utilizables()


def fusionar_cromosomas(cromosoma1: Cromosoma, cromosoma2: Cromosoma) -> Cromosoma:
    """
    Fusiona dos cromosomas en uno nuevo que contiene todos los patrones de ambos.
    
    Esta función es útil para operadores genéticos como el cruce.
    
    Args:
        cromosoma1: Primer cromosoma a fusionar.
        cromosoma2: Segundo cromosoma a fusionar.
    
    Returns:
        Cromosoma: Un nuevo cromosoma que contiene todos los patrones de ambos cromosomas.
    """
    # Crear una copia profunda de los patrones de ambos cromosomas
    patrones_combinados = deepcopy(cromosoma1.patrones + cromosoma2.patrones)
    
    # Crear y retornar un nuevo cromosoma con los patrones combinados
    return Cromosoma(patrones_combinados)


def crear_cromosoma_desde_dict(datos_cromosoma: List[Dict[str, Any]], longitud_minima_desperdicio: float = LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE) -> Cromosoma:
    """
    Crea un cromosoma a partir de una estructura de datos tipo diccionario.
    
    Esta función es útil para convertir datos JSON o diccionarios a objetos Cromosoma.
    
    Args:
        datos_cromosoma: Lista de diccionarios, cada uno representando un patrón.
            Cada patrón debe tener 'origen_barra_longitud', 'origen_barra_tipo' y 'piezas_cortadas'.
        longitud_minima_desperdicio: Longitud mínima para considerar un desperdicio utilizable.
    
    Returns:
        Cromosoma: Un nuevo cromosoma creado a partir de los datos proporcionados.
    """
    patrones = []
    
    for datos_patron in datos_cromosoma:
        origen_longitud = datos_patron['origen_barra_longitud']
        origen_tipo = datos_patron['origen_barra_tipo']
        piezas_cortadas = datos_patron['piezas_cortadas']
        
        patron = Patron(origen_longitud, origen_tipo, piezas_cortadas)
        patrones.append(patron)
    
    return Cromosoma(patrones)


def convertir_cromosoma_a_dict(cromosoma: Cromosoma) -> List[Dict[str, Any]]:
    """
    Convierte un cromosoma a una estructura de datos tipo diccionario.
    
    Esta función es útil para serializar un cromosoma a JSON o para visualización.
    
    Args:
        cromosoma: El cromosoma a convertir.
    
    Returns:
        List[Dict[str, Any]]: Lista de diccionarios, cada uno representando un patrón.
    """
    result = []
    
    for patron in cromosoma.patrones:
        patron_dict = {
            'origen_barra_longitud': patron.origen_barra_longitud,
            'origen_barra_tipo': patron.origen_barra_tipo,
            'piezas_cortadas': deepcopy(patron.piezas_cortadas),
            'desperdicio_patron_longitud': patron.desperdicio_patron_longitud,
            'es_desperdicio_utilizable': patron.es_desperdicio_utilizable
        }
        result.append(patron_dict)
    
    return result 
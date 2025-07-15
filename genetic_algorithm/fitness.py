"""
Módulo para la función de fitness del algoritmo genético.

Este módulo implementa la función de fitness y funciones auxiliares para evaluar
la calidad de las soluciones (cromosomas) en el algoritmo genético.
"""

from typing import Dict, Tuple, Any, Optional
import pandas as pd

from .chromosome import Cromosoma
from .chromosome_utils import calcular_sumario_piezas_en_cromosoma


def obtener_config_fitness_default() -> Dict[str, float]:
    """
    Proporciona una configuración por defecto para los pesos de los factores de fitness.
    
    Los valores están calibrados para que las penalizaciones por no cumplir la demanda
    sean significativamente más altas que las penalizaciones por desperdicio.
    CORECCIÓN: Se aumenta considerablemente la penalización por número de barras
    para forzar la búsqueda de soluciones que minimicen realmente el desperdicio.
    
    Returns:
        Dict[str, float]: Diccionario con la configuración por defecto.
    """
    return {
        'peso_desperdicio': 10.0,                # Factor base para el desperdicio (aumentado)
        'penalizacion_faltantes': 10000.0,       # Penalización por cada unidad de longitud faltante (aumentado)
        'penalizacion_sobrantes': 5000.0,        # Penalización por cada unidad de longitud producida en exceso (aumentado)
        'penalizacion_num_barras_estandar': 50.0, # Penalización por cada barra estándar utilizada (AUMENTADO SIGNIFICATIVAMENTE)
        'bonificacion_uso_desperdicios': 30.0    # Bonificación por cada unidad de longitud de desperdicios utilizados (aumentado)
    }


def calcular_penalizacion_faltantes(
    sumario_piezas: Dict[Tuple[Any, float], int],
    piezas_requeridas_df: pd.DataFrame,
    peso: float
) -> float:
    """
    Calcula la penalización por piezas faltantes (no cumplir con la demanda).
    
    Args:
        sumario_piezas: Diccionario con el resumen de piezas en el cromosoma.
            Las claves son tuplas (id_pedido, longitud_pieza) y los valores son las cantidades.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
            Debe tener columnas 'id_pedido', 'longitud_pieza_requerida' y 'cantidad_requerida'.
        peso: Factor de penalización por unidad de longitud faltante.
    
    Returns:
        float: Valor de la penalización por piezas faltantes.
    """
    penalizacion_total = 0.0
    
    # Calcular faltantes para cada pieza requerida
    for _, fila in piezas_requeridas_df.iterrows():
        id_pedido = fila['id_pedido']
        longitud = fila['longitud_pieza_requerida']
        cantidad_requerida = fila['cantidad_requerida']
        
        # Cantidad de esta pieza en el cromosoma
        cantidad_en_cromosoma = sumario_piezas.get((id_pedido, longitud), 0)
        
        # Si hay faltantes, aplicar penalización
        cantidad_faltante = max(0, cantidad_requerida - cantidad_en_cromosoma)
        if cantidad_faltante > 0:
            # La penalización es proporcional a la longitud y cantidad faltante
            penalizacion_total += cantidad_faltante * longitud * peso
    
    return penalizacion_total


def calcular_penalizacion_sobrantes(
    sumario_piezas: Dict[Tuple[Any, float], int],
    piezas_requeridas_df: pd.DataFrame,
    peso: float
) -> float:
    """
    Calcula la penalización por piezas sobrantes (producir más de lo necesario).
    
    Args:
        sumario_piezas: Diccionario con el resumen de piezas en el cromosoma.
            Las claves son tuplas (id_pedido, longitud_pieza) y los valores son las cantidades.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
            Debe tener columnas 'id_pedido', 'longitud_pieza_requerida' y 'cantidad_requerida'.
        peso: Factor de penalización por unidad de longitud sobrante.
    
    Returns:
        float: Valor de la penalización por piezas sobrantes.
    """
    penalizacion_total = 0.0
    
    # Crear un diccionario de piezas requeridas para búsqueda rápida
    piezas_requeridas = {}
    for _, fila in piezas_requeridas_df.iterrows():
        clave = (fila['id_pedido'], fila['longitud_pieza_requerida'])
        piezas_requeridas[clave] = fila['cantidad_requerida']
    
    # Verificar cada pieza en el cromosoma
    for (id_pedido, longitud), cantidad_en_cromosoma in sumario_piezas.items():
        clave = (id_pedido, longitud)
        
        # Si la pieza está en los requerimientos, verificar exceso
        if clave in piezas_requeridas:
            cantidad_requerida = piezas_requeridas[clave]
            cantidad_sobrante = max(0, cantidad_en_cromosoma - cantidad_requerida)
            if cantidad_sobrante > 0:
                penalizacion_total += cantidad_sobrante * longitud * peso
        else:
            # Si la pieza no está en los requerimientos, todo es sobrante
            penalizacion_total += cantidad_en_cromosoma * longitud * peso
    
    return penalizacion_total


def calcular_penalizacion_barras_usadas(
    cromosoma: Cromosoma,
    peso: float
) -> float:
    """
    Calcula la penalización por usar barras estándar.
    
    Args:
        cromosoma: El cromosoma a evaluar.
        peso: Factor de penalización por cada barra estándar utilizada.
    
    Returns:
        float: Valor de la penalización por barras estándar utilizadas.
    """
    # Contar el número de barras estándar utilizadas
    num_barras_estandar = cromosoma.contar_barras_estandar()
    
    return num_barras_estandar * peso


def calcular_bonificacion_uso_desperdicios(
    cromosoma: Cromosoma,
    peso: float
) -> float:
    """
    Calcula la bonificación por usar desperdicios previos.
    
    Args:
        cromosoma: El cromosoma a evaluar.
        peso: Factor de bonificación por cada unidad de longitud de desperdicios utilizados.
    
    Returns:
        float: Valor de la bonificación por uso de desperdicios.
    """
    # Calcular la longitud total de desperdicios utilizados
    longitud_desperdicios_usados = cromosoma.longitud_total_desperdicios_usados()
    
    return longitud_desperdicios_usados * peso


def calcular_fitness(
    cromosoma: Cromosoma,
    piezas_requeridas_df: pd.DataFrame,
    config_fitness: Optional[Dict[str, float]] = None
) -> float:
    """
    Calcula el valor de fitness de un cromosoma.
    
    El fitness evalúa la calidad de la solución, considerando el desperdicio generado,
    el cumplimiento de la demanda y otros factores. Un valor menor indica una mejor solución.
    
    Args:
        cromosoma: El cromosoma a evaluar.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
            Debe tener columnas 'id_pedido', 'longitud_pieza_requerida' y 'cantidad_requerida'.
        config_fitness: Diccionario con los pesos de los factores.
            Si no se proporciona, se utiliza la configuración por defecto.
    
    Returns:
        float: Valor de fitness del cromosoma (menor es mejor).
    """
    # Usar configuración por defecto si no se proporciona
    if config_fitness is None:
        config_fitness = obtener_config_fitness_default()
    
    # Calcular el sumario de piezas en el cromosoma
    sumario_piezas = calcular_sumario_piezas_en_cromosoma(cromosoma)
    
    # Calcular el desperdicio total
    desperdicio_total = cromosoma.calcular_desperdicio_total()
    valor_desperdicio = desperdicio_total * config_fitness.get('peso_desperdicio', 1.0)
    
    # Calcular penalizaciones
    valor_penalizacion_faltantes = calcular_penalizacion_faltantes(
        sumario_piezas,
        piezas_requeridas_df,
        config_fitness.get('penalizacion_faltantes', 1000.0)
    )
    
    valor_penalizacion_sobrantes = calcular_penalizacion_sobrantes(
        sumario_piezas,
        piezas_requeridas_df,
        config_fitness.get('penalizacion_sobrantes', 500.0)
    )
    
    valor_penalizacion_barras = calcular_penalizacion_barras_usadas(
        cromosoma,
        config_fitness.get('penalizacion_num_barras_estandar', 5.0)
    )
    
    # Calcular bonificaciones (se restan del fitness porque menor es mejor)
    valor_bonificacion_desperdicios = calcular_bonificacion_uso_desperdicios(
        cromosoma,
        config_fitness.get('bonificacion_uso_desperdicios', 3.0)
    )
    
    # Calcular fitness total (suma de penalizaciones - bonificaciones)
    fitness = (
        valor_desperdicio +
        valor_penalizacion_faltantes +
        valor_penalizacion_sobrantes +
        valor_penalizacion_barras -
        valor_bonificacion_desperdicios
    )
    
    return fitness


def analizar_componentes_fitness(
    cromosoma: Cromosoma,
    piezas_requeridas_df: pd.DataFrame,
    config_fitness: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Analiza los componentes individuales del fitness de un cromosoma.
    
    Esta función es útil para entender la contribución de cada factor al fitness total.
    
    Args:
        cromosoma: El cromosoma a evaluar.
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        config_fitness: Diccionario con los pesos de los factores.
    
    Returns:
        Dict[str, float]: Diccionario con los valores de cada componente del fitness.
    """
    # Usar configuración por defecto si no se proporciona
    if config_fitness is None:
        config_fitness = obtener_config_fitness_default()
    
    # Calcular el sumario de piezas en el cromosoma
    sumario_piezas = calcular_sumario_piezas_en_cromosoma(cromosoma)
    
    # Calcular componentes
    desperdicio_total = cromosoma.calcular_desperdicio_total()
    valor_desperdicio = desperdicio_total * config_fitness.get('peso_desperdicio', 1.0)
    
    valor_penalizacion_faltantes = calcular_penalizacion_faltantes(
        sumario_piezas,
        piezas_requeridas_df,
        config_fitness.get('penalizacion_faltantes', 1000.0)
    )
    
    valor_penalizacion_sobrantes = calcular_penalizacion_sobrantes(
        sumario_piezas,
        piezas_requeridas_df,
        config_fitness.get('penalizacion_sobrantes', 500.0)
    )
    
    valor_penalizacion_barras = calcular_penalizacion_barras_usadas(
        cromosoma,
        config_fitness.get('penalizacion_num_barras_estandar', 5.0)
    )
    
    valor_bonificacion_desperdicios = calcular_bonificacion_uso_desperdicios(
        cromosoma,
        config_fitness.get('bonificacion_uso_desperdicios', 3.0)
    )
    
    # Calcular fitness total
    fitness_total = (
        valor_desperdicio +
        valor_penalizacion_faltantes +
        valor_penalizacion_sobrantes +
        valor_penalizacion_barras -
        valor_bonificacion_desperdicios
    )
    
    return {
        'fitness_total': fitness_total,
        'desperdicio': valor_desperdicio,
        'penalizacion_faltantes': valor_penalizacion_faltantes,
        'penalizacion_sobrantes': valor_penalizacion_sobrantes,
        'penalizacion_barras': valor_penalizacion_barras,
        'bonificacion_desperdicios': valor_bonificacion_desperdicios,
        'desperdicio_sin_peso': desperdicio_total,
        'numero_barras_estandar': cromosoma.contar_barras_estandar(),
        'longitud_desperdicios_usados': cromosoma.longitud_total_desperdicios_usados()
    } 
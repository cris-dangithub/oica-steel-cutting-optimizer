"""
Adaptador de entrada para el algoritmo genético.

Este módulo convierte los datos del formato usado en main.py al formato
esperado por el algoritmo genético.
"""

from typing import List, Dict, Any, Tuple
import pandas as pd


def adaptar_entrada_para_ag(
    piezas_df: pd.DataFrame,
    barras_disponibles: List[float],
    desperdicios_previos: List[float]
) -> Tuple[pd.DataFrame, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Adapta los datos de entrada del formato de main.py al formato del AG.
    
    Args:
        piezas_df: DataFrame con columnas ['id_pedido', 'longitud_pieza_requerida', 'cantidad_requerida']
        barras_disponibles: Lista de longitudes de barras estándar disponibles
        desperdicios_previos: Lista de longitudes de desperdicios de grupos anteriores
    
    Returns:
        Tuple: (piezas_requeridas_df, barras_estandar_disponibles, desperdicios_reutilizables_previos)
    """
    # Validar entrada
    if not validar_entrada_ag(piezas_df, barras_disponibles, desperdicios_previos):
        raise ValueError("Los datos de entrada no son válidos")
    
    # El DataFrame de piezas ya está en el formato correcto, solo necesitamos validar columnas
    piezas_requeridas_df = piezas_df.copy()
    
    # Asegurar que las columnas tengan los nombres correctos
    if 'longitud_pieza_requerida' in piezas_requeridas_df.columns:
        # Ya está en formato correcto
        pass
    elif 'longitud' in piezas_requeridas_df.columns:
        # Renombrar si viene con nombre alternativo
        piezas_requeridas_df = piezas_requeridas_df.rename(columns={'longitud': 'longitud_pieza_requerida'})
    
    # Convertir barras disponibles a formato de diccionarios
    barras_estandar_disponibles = longitudes_a_barras_dict(barras_disponibles)
    
    # Convertir desperdicios a formato de diccionarios
    desperdicios_reutilizables_previos = longitudes_a_desperdicios_dict(desperdicios_previos)
    
    return piezas_requeridas_df, barras_estandar_disponibles, desperdicios_reutilizables_previos


def longitudes_a_barras_dict(longitudes: List[float]) -> List[Dict[str, Any]]:
    """
    Convierte una lista de longitudes a formato de diccionarios para barras estándar.
    
    Args:
        longitudes: Lista de longitudes de barras estándar
    
    Returns:
        List[Dict]: Lista de diccionarios con formato para el AG
    """
    barras_dict = []
    
    for longitud in longitudes:
        if longitud > 0:  # Solo incluir longitudes válidas
            barras_dict.append({
                'longitud': float(longitud),
                'tipo': 'estandar'
            })
    
    return barras_dict


def longitudes_a_desperdicios_dict(longitudes: List[float]) -> List[Dict[str, Any]]:
    """
    Convierte una lista de longitudes a formato de diccionarios para desperdicios.
    
    Args:
        longitudes: Lista de longitudes de desperdicios
    
    Returns:
        List[Dict]: Lista de diccionarios con formato para el AG
    """
    desperdicios_dict = []
    
    for longitud in longitudes:
        if longitud > 0:  # Solo incluir longitudes válidas
            desperdicios_dict.append({
                'longitud': float(longitud),
                'tipo': 'desperdicio'
            })
    
    return desperdicios_dict


def validar_entrada_ag(
    piezas_df: pd.DataFrame,
    barras_disponibles: List[float],
    desperdicios_previos: List[float]
) -> bool:
    """
    Valida que los datos de entrada sean correctos para el AG.
    
    Args:
        piezas_df: DataFrame de piezas requeridas
        barras_disponibles: Lista de longitudes de barras
        desperdicios_previos: Lista de longitudes de desperdicios
    
    Returns:
        bool: True si los datos son válidos, False en caso contrario
    """
    # Validar DataFrame de piezas
    if not isinstance(piezas_df, pd.DataFrame):
        return False
    
    if piezas_df.empty:
        return False
    
    # Verificar columnas requeridas
    columnas_requeridas = ['id_pedido', 'cantidad_requerida']
    columnas_longitud = ['longitud_pieza_requerida', 'longitud']  # Aceptar ambos nombres
    
    for col in columnas_requeridas:
        if col not in piezas_df.columns:
            return False
    
    # Verificar que al menos una columna de longitud esté presente
    if not any(col in piezas_df.columns for col in columnas_longitud):
        return False
    
    # Validar tipos de datos en el DataFrame
    try:
        # Verificar que cantidad_requerida sea numérica y positiva
        if not all(piezas_df['cantidad_requerida'] > 0):
            return False
        
        # Verificar que las longitudes sean numéricas y positivas
        col_longitud = 'longitud_pieza_requerida' if 'longitud_pieza_requerida' in piezas_df.columns else 'longitud'
        if not all(piezas_df[col_longitud] > 0):
            return False
            
    except (TypeError, ValueError):
        return False
    
    # Validar barras disponibles
    if not isinstance(barras_disponibles, list):
        return False
    
    for barra in barras_disponibles:
        if not isinstance(barra, (int, float)) or barra <= 0:
            return False
    
    # Validar desperdicios previos
    if not isinstance(desperdicios_previos, list):
        return False
    
    for desperdicio in desperdicios_previos:
        if not isinstance(desperdicio, (int, float)) or desperdicio <= 0:
            return False
    
    return True


def limpiar_datos_entrada(
    piezas_df: pd.DataFrame,
    barras_disponibles: List[float],
    desperdicios_previos: List[float],
    longitud_minima_desperdicio: float = 0.5
) -> Tuple[pd.DataFrame, List[float], List[float]]:
    """
    Limpia y normaliza los datos de entrada.
    
    Args:
        piezas_df: DataFrame de piezas requeridas
        barras_disponibles: Lista de longitudes de barras
        desperdicios_previos: Lista de longitudes de desperdicios
        longitud_minima_desperdicio: Longitud mínima para considerar desperdicios
    
    Returns:
        Tuple: Datos limpiados y normalizados
    """
    # Limpiar DataFrame de piezas
    piezas_limpio = piezas_df.copy()
    
    # Asegurar que cantidad_requerida sea entero
    piezas_limpio['cantidad_requerida'] = piezas_limpio['cantidad_requerida'].astype(int)
    
    # Redondear longitudes a 3 decimales
    col_longitud = 'longitud_pieza_requerida' if 'longitud_pieza_requerida' in piezas_limpio.columns else 'longitud'
    piezas_limpio[col_longitud] = piezas_limpio[col_longitud].round(3)
    
    # Eliminar filas con cantidad 0 o negativa
    piezas_limpio = piezas_limpio[piezas_limpio['cantidad_requerida'] > 0]
    
    # Limpiar barras disponibles
    barras_limpias = []
    for barra in barras_disponibles:
        if barra > 0:
            barras_limpias.append(round(float(barra), 3))
    
    # Eliminar duplicados y ordenar
    barras_limpias = sorted(list(set(barras_limpias)), reverse=True)
    
    # Limpiar desperdicios previos
    desperdicios_limpios = []
    for desperdicio in desperdicios_previos:
        if desperdicio >= longitud_minima_desperdicio:
            desperdicios_limpios.append(round(float(desperdicio), 3))
    
    # Eliminar duplicados y ordenar
    desperdicios_limpios = sorted(list(set(desperdicios_limpios)), reverse=True)
    
    return piezas_limpio, barras_limpias, desperdicios_limpios


def consolidar_piezas_identicas(piezas_df: pd.DataFrame) -> pd.DataFrame:
    """
    Consolida piezas idénticas sumando sus cantidades.
    
    Args:
        piezas_df: DataFrame de piezas requeridas
    
    Returns:
        pd.DataFrame: DataFrame con piezas consolidadas
    """
    col_longitud = 'longitud_pieza_requerida' if 'longitud_pieza_requerida' in piezas_df.columns else 'longitud'
    
    # Agrupar por id_pedido y longitud, sumando cantidades
    piezas_consolidadas = piezas_df.groupby(['id_pedido', col_longitud], as_index=False)['cantidad_requerida'].sum()
    
    return piezas_consolidadas


def expandir_piezas_multiples(piezas_df: pd.DataFrame) -> pd.DataFrame:
    """
    Expande piezas con cantidad > 1 en filas individuales.
    
    Esta función es útil para algunos algoritmos que trabajan mejor
    con piezas individuales en lugar de cantidades agrupadas.
    
    Args:
        piezas_df: DataFrame de piezas requeridas
    
    Returns:
        pd.DataFrame: DataFrame con piezas expandidas
    """
    col_longitud = 'longitud_pieza_requerida' if 'longitud_pieza_requerida' in piezas_df.columns else 'longitud'
    
    filas_expandidas = []
    
    for _, fila in piezas_df.iterrows():
        cantidad = int(fila['cantidad_requerida'])
        for i in range(int(cantidad)):
            nueva_fila = fila.copy()
            nueva_fila['cantidad_requerida'] = 1
            # Añadir sufijo al id_pedido para mantener unicidad
            if cantidad > 1:
                nueva_fila['id_pedido'] = f"{fila['id_pedido']}_{i+1}"
            filas_expandidas.append(nueva_fila)
    
    return pd.DataFrame(filas_expandidas)


def generar_resumen_entrada(
    piezas_df: pd.DataFrame,
    barras_disponibles: List[float],
    desperdicios_previos: List[float]
) -> Dict[str, Any]:
    """
    Genera un resumen de los datos de entrada.
    
    Args:
        piezas_df: DataFrame de piezas requeridas
        barras_disponibles: Lista de longitudes de barras
        desperdicios_previos: Lista de longitudes de desperdicios
    
    Returns:
        Dict: Resumen de los datos de entrada
    """
    col_longitud = 'longitud_pieza_requerida' if 'longitud_pieza_requerida' in piezas_df.columns else 'longitud'
    
    # Estadísticas de piezas
    total_piezas_tipos = len(piezas_df)
    total_piezas_cantidad = piezas_df['cantidad_requerida'].sum()
    longitud_total_piezas = (piezas_df[col_longitud] * piezas_df['cantidad_requerida']).sum()
    longitud_promedio_pieza = piezas_df[col_longitud].mean()
    longitud_min_pieza = piezas_df[col_longitud].min()
    longitud_max_pieza = piezas_df[col_longitud].max()
    
    # Estadísticas de barras
    total_tipos_barras = len(set(barras_disponibles))
    longitud_promedio_barra = sum(barras_disponibles) / len(barras_disponibles) if barras_disponibles else 0
    longitud_min_barra = min(barras_disponibles) if barras_disponibles else 0
    longitud_max_barra = max(barras_disponibles) if barras_disponibles else 0
    
    # Estadísticas de desperdicios
    total_desperdicios = len(desperdicios_previos)
    longitud_total_desperdicios = sum(desperdicios_previos)
    longitud_promedio_desperdicio = longitud_total_desperdicios / total_desperdicios if total_desperdicios > 0 else 0
    
    return {
        'piezas': {
            'total_tipos': total_piezas_tipos,
            'total_cantidad': int(total_piezas_cantidad),
            'longitud_total': round(longitud_total_piezas, 3),
            'longitud_promedio': round(longitud_promedio_pieza, 3),
            'longitud_min': round(longitud_min_pieza, 3),
            'longitud_max': round(longitud_max_pieza, 3)
        },
        'barras_estandar': {
            'total_tipos': total_tipos_barras,
            'longitud_promedio': round(longitud_promedio_barra, 3),
            'longitud_min': round(longitud_min_barra, 3),
            'longitud_max': round(longitud_max_barra, 3)
        },
        'desperdicios_previos': {
            'total_cantidad': total_desperdicios,
            'longitud_total': round(longitud_total_desperdicios, 3),
            'longitud_promedio': round(longitud_promedio_desperdicio, 3)
        }
    }


def adaptar_entrada_completa(
    piezas_df: pd.DataFrame,
    barras_disponibles: List[float],
    desperdicios_previos: List[float],
    longitud_minima_desperdicio: float = 0.5,
    consolidar_piezas: bool = True,
    limpiar_datos: bool = True
) -> Tuple[pd.DataFrame, List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Adaptación completa de entrada con todas las opciones de procesamiento.
    
    Args:
        piezas_df: DataFrame de piezas requeridas
        barras_disponibles: Lista de longitudes de barras
        desperdicios_previos: Lista de longitudes de desperdicios
        longitud_minima_desperdicio: Longitud mínima para desperdicios
        consolidar_piezas: Si consolidar piezas idénticas
        limpiar_datos: Si limpiar y normalizar datos
    
    Returns:
        Tuple: (piezas_df, barras_dict, desperdicios_dict, resumen)
    """
    # Limpiar datos si se solicita
    if limpiar_datos:
        piezas_df, barras_disponibles, desperdicios_previos = limpiar_datos_entrada(
            piezas_df, barras_disponibles, desperdicios_previos, longitud_minima_desperdicio
        )
    
    # Consolidar piezas si se solicita
    if consolidar_piezas:
        piezas_df = consolidar_piezas_identicas(piezas_df)
    
    # Generar resumen antes de la adaptación
    resumen = generar_resumen_entrada(piezas_df, barras_disponibles, desperdicios_previos)
    
    # Adaptar al formato del AG
    piezas_adaptadas, barras_dict, desperdicios_dict = adaptar_entrada_para_ag(
        piezas_df, barras_disponibles, desperdicios_previos
    )
    
    return piezas_adaptadas, barras_dict, desperdicios_dict, resumen 
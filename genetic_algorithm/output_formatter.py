"""
Formateador de salida del algoritmo genético.

Este módulo convierte los resultados del algoritmo genético (objetos Cromosoma)
al formato esperado por el sistema principal en main.py.
"""

from typing import List, Dict, Any, Tuple
from .chromosome import Cromosoma, Patron


def formatear_salida_desde_cromosoma(
    mejor_cromosoma: Cromosoma,
    longitud_minima_desperdicio: float = 0.5
) -> Tuple[List[Dict[str, Any]], List[float]]:
    """
    Convierte un cromosoma del AG al formato esperado por main.py.
    
    Args:
        mejor_cromosoma: El mejor cromosoma encontrado por el algoritmo genético.
        longitud_minima_desperdicio: Longitud mínima para considerar un desperdicio utilizable.
    
    Returns:
        Tuple[List[Dict], List[float]]: (patrones_de_corte_generados, nuevos_desperdicios_utilizables)
    """
    if mejor_cromosoma is None or len(mejor_cromosoma.patrones) == 0:
        return [], []
    
    patrones_de_corte_generados = []
    nuevos_desperdicios_utilizables = []
    
    for patron in mejor_cromosoma.patrones:
        # Convertir patrón a formato de diccionario
        patron_dict = patron_a_dict(patron)
        patrones_de_corte_generados.append(patron_dict)
        
        # Extraer desperdicios utilizables
        if patron.es_desperdicio_utilizable and patron.desperdicio_patron_longitud >= longitud_minima_desperdicio:
            nuevos_desperdicios_utilizables.append(round(patron.desperdicio_patron_longitud, 3))
    
    # Validar formato de salida
    if not validar_formato_salida(patrones_de_corte_generados, nuevos_desperdicios_utilizables):
        raise ValueError("El formato de salida generado no es válido")
    
    return patrones_de_corte_generados, nuevos_desperdicios_utilizables


def patron_a_dict(patron: Patron) -> Dict[str, Any]:
    """
    Convierte un objeto Patron al formato de diccionario esperado por main.py.
    
    Args:
        patron: Objeto Patron del algoritmo genético.
    
    Returns:
        Dict: Diccionario con el formato esperado por main.py.
    """
    # Extraer cortes realizados (longitudes de las piezas cortadas)
    cortes_realizados = []
    piezas_obtenidas = []
    
    for pieza_info in patron.piezas_cortadas:
        longitud_pieza = pieza_info['longitud_pieza']
        cantidad_en_patron = pieza_info['cantidad_pieza_en_patron']
        id_pedido = pieza_info['id_pedido']
        
        # Añadir cada corte individual
        for _ in range(int(cantidad_en_patron)):
            cortes_realizados.append(longitud_pieza)
            piezas_obtenidas.append({
                'id_pedido': id_pedido,
                'longitud': longitud_pieza
            })
    
    return {
        'barra_origen_longitud': patron.origen_barra_longitud,
        'cortes_realizados': cortes_realizados,
        'piezas_obtenidas': piezas_obtenidas,
        'desperdicio_resultante': round(patron.desperdicio_patron_longitud, 3)
    }


def extraer_desperdicios_utilizables(
    cromosoma: Cromosoma,
    longitud_minima: float
) -> List[float]:
    """
    Extrae todos los desperdicios utilizables de un cromosoma.
    
    Args:
        cromosoma: Cromosoma del cual extraer desperdicios.
        longitud_minima: Longitud mínima para considerar un desperdicio utilizable.
    
    Returns:
        List[float]: Lista de longitudes de desperdicios utilizables.
    """
    desperdicios = []
    
    for patron in cromosoma.patrones:
        if patron.es_desperdicio_utilizable and patron.desperdicio_patron_longitud >= longitud_minima:
            desperdicios.append(round(patron.desperdicio_patron_longitud, 3))
    
    return sorted(desperdicios, reverse=True)  # Ordenar de mayor a menor


def validar_formato_salida(
    patrones: List[Dict[str, Any]],
    desperdicios: List[float]
) -> bool:
    """
    Valida que el formato de salida sea correcto.
    
    Args:
        patrones: Lista de patrones de corte generados.
        desperdicios: Lista de desperdicios utilizables.
    
    Returns:
        bool: True si el formato es válido, False en caso contrario.
    """
    # Validar que patrones sea una lista
    if not isinstance(patrones, list):
        return False
    
    # Validar que desperdicios sea una lista
    if not isinstance(desperdicios, list):
        return False
    
    # Validar cada patrón
    for patron in patrones:
        if not isinstance(patron, dict):
            return False
        
        # Verificar claves requeridas
        claves_requeridas = ['barra_origen_longitud', 'cortes_realizados', 'piezas_obtenidas', 'desperdicio_resultante']
        for clave in claves_requeridas:
            if clave not in patron:
                return False
        
        # Validar tipos de datos
        if not isinstance(patron['barra_origen_longitud'], (int, float)):
            return False
        
        if not isinstance(patron['cortes_realizados'], list):
            return False
        
        if not isinstance(patron['piezas_obtenidas'], list):
            return False
        
        if not isinstance(patron['desperdicio_resultante'], (int, float)):
            return False
        
        # Validar que todos los cortes sean números
        for corte in patron['cortes_realizados']:
            if not isinstance(corte, (int, float)):
                return False
        
        # Validar estructura de piezas obtenidas
        for pieza in patron['piezas_obtenidas']:
            if not isinstance(pieza, dict):
                return False
            if 'id_pedido' not in pieza or 'longitud' not in pieza:
                return False
            if not isinstance(pieza['longitud'], (int, float)):
                return False
        
        # Validar consistencia: número de cortes = número de piezas
        if len(patron['cortes_realizados']) != len(patron['piezas_obtenidas']):
            return False
        
        # Validar que la suma de cortes + desperdicio = longitud de barra origen
        suma_cortes = sum(patron['cortes_realizados'])
        total_esperado = suma_cortes + patron['desperdicio_resultante']
        if abs(total_esperado - patron['barra_origen_longitud']) > 0.001:  # Tolerancia para errores de redondeo
            return False
    
    # Validar desperdicios
    for desperdicio in desperdicios:
        if not isinstance(desperdicio, (int, float)):
            return False
        if desperdicio < 0:
            return False
    
    return True


def generar_resumen_patrones(patrones: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Genera un resumen estadístico de los patrones de corte.
    
    Args:
        patrones: Lista de patrones de corte.
    
    Returns:
        Dict: Resumen con estadísticas de los patrones.
    """
    if not patrones:
        return {
            'total_patrones': 0,
            'total_barras_utilizadas': 0,
            'total_piezas_cortadas': 0,
            'desperdicio_total': 0.0,
            'longitud_total_barras': 0.0,
            'longitud_total_piezas': 0.0,
            'eficiencia_material': 0.0
        }
    
    total_patrones = len(patrones)
    total_piezas_cortadas = sum(len(p['piezas_obtenidas']) for p in patrones)
    desperdicio_total = sum(p['desperdicio_resultante'] for p in patrones)
    longitud_total_barras = sum(p['barra_origen_longitud'] for p in patrones)
    longitud_total_piezas = longitud_total_barras - desperdicio_total
    
    # Calcular eficiencia de material
    eficiencia_material = (longitud_total_piezas / longitud_total_barras * 100) if longitud_total_barras > 0 else 0.0
    
    # Contar barras por tipo (estándar vs desperdicio)
    barras_estandar = 0
    barras_desperdicio = 0
    
    # Nota: En el formato actual no tenemos información del tipo de barra origen
    # Esto se podría mejorar en futuras versiones
    total_barras_utilizadas = total_patrones  # Asumimos una barra por patrón
    
    return {
        'total_patrones': total_patrones,
        'total_barras_utilizadas': total_barras_utilizadas,
        'total_piezas_cortadas': total_piezas_cortadas,
        'desperdicio_total': round(desperdicio_total, 3),
        'longitud_total_barras': round(longitud_total_barras, 3),
        'longitud_total_piezas': round(longitud_total_piezas, 3),
        'eficiencia_material': round(eficiencia_material, 2)
    }


def formatear_salida_con_metadatos(
    mejor_cromosoma: Cromosoma,
    estadisticas_evolucion: Dict[str, Any],
    longitud_minima_desperdicio: float = 0.5
) -> Dict[str, Any]:
    """
    Formatea la salida incluyendo metadatos del proceso de optimización.
    
    Args:
        mejor_cromosoma: El mejor cromosoma encontrado.
        estadisticas_evolucion: Estadísticas del proceso evolutivo.
        longitud_minima_desperdicio: Longitud mínima para desperdicios utilizables.
    
    Returns:
        Dict: Salida formateada con metadatos adicionales.
    """
    patrones, desperdicios = formatear_salida_desde_cromosoma(mejor_cromosoma, longitud_minima_desperdicio)
    resumen = generar_resumen_patrones(patrones)
    
    return {
        'patrones_de_corte': patrones,
        'desperdicios_utilizables': desperdicios,
        'resumen_patrones': resumen,
        'metadatos_optimizacion': {
            'algoritmo': 'genetico',
            'mejor_fitness': estadisticas_evolucion.get('mejor_fitness_global', None),
            'generaciones_ejecutadas': estadisticas_evolucion.get('generaciones_ejecutadas', None),
            'tiempo_ejecucion_segundos': estadisticas_evolucion.get('tiempo_total_segundos', None),
            'convergencia_detectada': estadisticas_evolucion.get('convergencia_detectada', None)
        }
    }


def convertir_cromosoma_a_formato_legacy(cromosoma: Cromosoma) -> List[Dict[str, Any]]:
    """
    Convierte un cromosoma al formato legacy usado en versiones anteriores.
    
    Esta función mantiene compatibilidad con sistemas que esperan el formato anterior.
    
    Args:
        cromosoma: Cromosoma a convertir.
    
    Returns:
        List[Dict]: Lista en formato legacy.
    """
    patrones_legacy = []
    
    for patron in cromosoma.patrones:
        patron_legacy = {
            'barra_origen': f"{patron.origen_barra_tipo}_{patron.origen_barra_longitud}m",
            'longitud_barra': patron.origen_barra_longitud,
            'tipo_barra': patron.origen_barra_tipo,
            'cortes': [],
            'desperdicio': patron.desperdicio_patron_longitud,
            'utilizable': patron.es_desperdicio_utilizable
        }
        
        for pieza_info in patron.piezas_cortadas:
            for _ in range(pieza_info['cantidad_pieza_en_patron']):
                patron_legacy['cortes'].append({
                    'pedido': pieza_info['id_pedido'],
                    'longitud': pieza_info['longitud_pieza']
                })
        
        patrones_legacy.append(patron_legacy)
    
    return patrones_legacy 
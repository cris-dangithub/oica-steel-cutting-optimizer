"""
Paquete para el Algoritmo Genético del Optimizador Inteligente de Cortes de Acero (OICA).

Este paquete contiene todos los componentes necesarios para el algoritmo genético:
- Representación de cromosomas
- Funciones de fitness
- Operadores genéticos (selección, cruce, mutación)
- Motor de ejecución
- Utilidades y herramientas auxiliares
"""

# Constantes globales
LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE = 0.5  # Metros. Desperdicios menores se consideran pérdida.

# Configuración por defecto para los operadores genéticos
CONFIG_OPERADORES_DEFAULT = {
    'tamaño_poblacion': 50,
    'estrategia_inicializacion': 'hibrida',
    'proporcion_heuristicos': 0.6,
    'metodo_seleccion': 'torneo',
    'tamaño_torneo': 3,
    'tasa_cruce': 0.8,
    'estrategia_cruce': 'un_punto',
    'tasa_mutacion_individuo': 0.2,
    'tasa_mutacion_gen': 0.1,
    'operaciones_mutacion': ['cambiar_origen', 'reoptimizar', 'mover_pieza'],
    'reparar_hijos_cruce': True
}

# Configuración por defecto para el ciclo evolutivo
CONFIG_CICLO_EVOLUTIVO_DEFAULT = {
    # Criterios de parada
    'max_generaciones': 100,
    'criterio_convergencia': 'generaciones_sin_mejora',
    'generaciones_sin_mejora_max': 20,
    'fitness_objetivo': None,
    'tiempo_limite_segundos': 300,
    'diversidad_minima': 0.01,
    
    # Elitismo y reemplazo
    'elitismo': True,
    'tamaño_elite': 2,
    'estrategia_reemplazo': 'elitismo',
    
    # Logging y monitoreo
    'logging_habilitado': True,
    'logging_frecuencia': 10,
    'guardar_mejor_por_generacion': True,
    
    # Optimizaciones
    'paralelizar_evaluacion': False,
    'cache_fitness': False
}

# Configuración por defecto para el algoritmo genético completo
CONFIG_GA_DEFAULT = {
    **CONFIG_OPERADORES_DEFAULT,
    **CONFIG_CICLO_EVOLUTIVO_DEFAULT
} 
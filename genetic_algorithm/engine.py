"""
Motor principal del algoritmo genético.

Este módulo implementa el núcleo del algoritmo genético que orquesta
todos los operadores y gestiona el ciclo evolutivo completo.
"""

import time
import random
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from .chromosome import Cromosoma
from .population import inicializar_poblacion
from .fitness import calcular_fitness
from .selection import seleccionar_padres, seleccionar_parejas_para_cruce
from .crossover import cruzar
from .mutation import mutar
from .metrics import RegistroEvolucion, detectar_convergencia
from . import CONFIG_GA_DEFAULT


def ejecutar_algoritmo_genetico(
    piezas_requeridas_df: pd.DataFrame,
    barras_estandar_disponibles: List[Dict[str, Any]],
    desperdicios_reutilizables_previos: List[Dict[str, Any]],
    config_ga: Optional[Dict[str, Any]] = None
) -> Tuple[Cromosoma, Dict[str, Any]]:
    """
    Ejecuta el algoritmo genético completo para optimizar el corte de acero.
    
    Args:
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        barras_estandar_disponibles: Lista de barras estándar disponibles.
        desperdicios_reutilizables_previos: Lista de desperdicios reutilizables.
        config_ga: Configuración del algoritmo genético.
    
    Returns:
        Tuple[Cromosoma, Dict]: Mejor cromosoma encontrado y estadísticas de evolución.
    """
    # Configuración por defecto
    if config_ga is None:
        config_ga = CONFIG_GA_DEFAULT.copy()
    else:
        # Combinar configuración proporcionada con valores por defecto
        config_completa = CONFIG_GA_DEFAULT.copy()
        config_completa.update(config_ga)
        config_ga = config_completa
    
    # Inicializar registro de evolución
    registro = RegistroEvolucion()
    registro.iniciar_registro(config_ga)
    
    if config_ga.get('logging_habilitado', True):
        print("Iniciando Algoritmo Genético...")
        print(f"Configuración: {config_ga['tamaño_poblacion']} individuos, "
              f"{config_ga['max_generaciones']} generaciones máx.")
    
    try:
        # Paso 1: Inicializar población
        poblacion = inicializar_poblacion(
            tamaño_poblacion=config_ga['tamaño_poblacion'],
            piezas_requeridas_df=piezas_requeridas_df,
            barras_estandar_disponibles=barras_estandar_disponibles,
            desperdicios_reutilizables_previos=desperdicios_reutilizables_previos,
            estrategia_inicializacion=config_ga['estrategia_inicializacion'],
            config_ga=config_ga
        )
        
        # Paso 2: Evaluar población inicial
        valores_fitness = []
        for cromosoma in poblacion:
            fitness = calcular_fitness(cromosoma, piezas_requeridas_df)
            valores_fitness.append(fitness)
        
        # Registrar generación inicial
        registro.registrar_generacion(0, poblacion, valores_fitness, 0.0)
        
        # Paso 3: Bucle evolutivo principal
        generacion = 1
        tiempo_inicio_total = time.time()
        
        while generacion <= config_ga['max_generaciones']:
            tiempo_inicio_generacion = time.time()
            
            # Verificar criterios de parada
            if verificar_criterios_parada(
                generacion, 
                registro.mejor_fitness_por_generacion,
                tiempo_inicio_total,
                config_ga
            ):
                if config_ga.get('logging_habilitado', True):
                    print(f"Criterio de parada alcanzado en generación {generacion}")
                break
            
            # Paso 3.1: Selección de padres
            num_padres = config_ga['tamaño_poblacion']
            if config_ga['elitismo']:
                # Reservar espacio para élite
                num_padres = config_ga['tamaño_poblacion'] - config_ga['tamaño_elite']
            
            padres = seleccionar_padres(
                poblacion=poblacion,
                valores_fitness=valores_fitness,
                numero_de_padres_a_seleccionar=num_padres,
                metodo_seleccion=config_ga['metodo_seleccion'],
                tamaño_torneo=config_ga['tamaño_torneo']
            )
            
            # Paso 3.2: Formar parejas y aplicar cruce
            hijos = []
            if len(padres) >= 2:
                parejas = seleccionar_parejas_para_cruce(padres, 'aleatorio')
                
                for padre1, padre2 in parejas:
                    hijo1, hijo2 = cruzar(
                        padre1_cromosoma=padre1,
                        padre2_cromosoma=padre2,
                        piezas_requeridas_df=piezas_requeridas_df,
                        tasa_cruce=config_ga['tasa_cruce'],
                        estrategia_cruce=config_ga['estrategia_cruce'],
                        config_ga={
                            **config_ga,
                            'barras_disponibles': barras_estandar_disponibles,
                            'desperdicios_disponibles': desperdicios_reutilizables_previos
                        }
                    )
                    hijos.extend([hijo1, hijo2])
            else:
                # Si hay muy pocos padres, clonar los existentes
                for padre in padres:
                    hijos.append(padre.clonar())
                    if len(hijos) < num_padres:
                        hijos.append(padre.clonar())
            
            # Ajustar número de hijos si es necesario
            if len(hijos) > num_padres:
                hijos = hijos[:num_padres]
            elif len(hijos) < num_padres:
                # Completar con padres adicionales si es necesario
                while len(hijos) < num_padres:
                    hijos.append(random.choice(padres).clonar())
            
            # Paso 3.3: Aplicar mutación
            hijos_mutados = []
            for hijo in hijos:
                hijo_mutado = mutar(
                    cromosoma=hijo,
                    piezas_requeridas_df=piezas_requeridas_df,
                    barras_estandar_disponibles=barras_estandar_disponibles,
                    desperdicios_reutilizables_previos=desperdicios_reutilizables_previos,
                    tasa_mutacion_individuo=config_ga['tasa_mutacion_individuo'],
                    tasa_mutacion_gen=config_ga['tasa_mutacion_gen'],
                    config_ga=config_ga
                )
                hijos_mutados.append(hijo_mutado)
            
            # Paso 3.4: Evaluar nueva generación
            valores_fitness_hijos = []
            for hijo in hijos_mutados:
                fitness = calcular_fitness(hijo, piezas_requeridas_df)
                valores_fitness_hijos.append(fitness)
            
            # Paso 3.5: Aplicar elitismo y reemplazo generacional
            nueva_poblacion, nuevos_valores_fitness = aplicar_elitismo_y_reemplazo(
                poblacion_actual=poblacion,
                valores_fitness_actual=valores_fitness,
                poblacion_hijos=hijos_mutados,
                valores_fitness_hijos=valores_fitness_hijos,
                config_ga=config_ga
            )
            
            # Actualizar población
            poblacion = nueva_poblacion
            valores_fitness = nuevos_valores_fitness
            
            # Registrar estadísticas de la generación
            tiempo_generacion = time.time() - tiempo_inicio_generacion
            registro.registrar_generacion(generacion, poblacion, valores_fitness, tiempo_generacion)
            
            generacion += 1
        
        # Finalizar registro
        registro.finalizar_registro()
        
        if config_ga.get('logging_habilitado', True):
            print(f"Algoritmo genético completado en {registro.tiempo_total:.2f} segundos")
            print(f"Mejor fitness: {registro.mejor_fitness_global:.4f}")
        
        return registro.mejor_cromosoma_global, registro.obtener_resumen()
    
    except Exception as e:
        registro.finalizar_registro()
        if config_ga.get('logging_habilitado', True):
            print(f"Error durante la ejecución del algoritmo genético: {e}")
        raise


def verificar_criterios_parada(
    generacion_actual: int,
    historial_mejor_fitness: List[float],
    tiempo_inicio: float,
    config_ga: Dict[str, Any]
) -> bool:
    """
    Verifica si se debe detener el algoritmo genético.
    
    Args:
        generacion_actual: Número de la generación actual.
        historial_mejor_fitness: Lista de mejores fitness por generación.
        tiempo_inicio: Tiempo de inicio del algoritmo.
        config_ga: Configuración del algoritmo genético.
    
    Returns:
        bool: True si se debe detener, False en caso contrario.
    """
    # Criterio 1: Número máximo de generaciones
    if generacion_actual >= config_ga.get('max_generaciones', 100):
        return True
    
    # Criterio 2: Tiempo límite
    tiempo_transcurrido = time.time() - tiempo_inicio
    if tiempo_transcurrido >= config_ga.get('tiempo_limite_segundos', 300):
        return True
    
    # Criterio 3: Fitness objetivo alcanzado
    fitness_objetivo = config_ga.get('fitness_objetivo')
    if fitness_objetivo is not None:
        if len(historial_mejor_fitness) > 0:
            mejor_actual = min(historial_mejor_fitness)
            if mejor_actual <= fitness_objetivo:
                return True
    
    # Criterio 4: Convergencia por generaciones sin mejora
    if config_ga.get('criterio_convergencia') == 'generaciones_sin_mejora':
        if detectar_convergencia(
            historial_mejor_fitness,
            config_ga.get('generaciones_sin_mejora_max', 20),
            0.001  # Umbral de mejora mínima
        ):
            return True
    
    return False


def aplicar_elitismo_y_reemplazo(
    poblacion_actual: List[Cromosoma],
    valores_fitness_actual: List[float],
    poblacion_hijos: List[Cromosoma],
    valores_fitness_hijos: List[float],
    config_ga: Dict[str, Any]
) -> Tuple[List[Cromosoma], List[float]]:
    """
    Aplica elitismo y reemplazo generacional.
    
    Args:
        poblacion_actual: Población de la generación actual.
        valores_fitness_actual: Fitness de la población actual.
        poblacion_hijos: Población de hijos generada.
        valores_fitness_hijos: Fitness de los hijos.
        config_ga: Configuración del algoritmo genético.
    
    Returns:
        Tuple: Nueva población y sus valores de fitness.
    """
    if not config_ga['elitismo']:
        # Reemplazo completo: los hijos reemplazan completamente a los padres
        return poblacion_hijos, valores_fitness_hijos
    
    # Aplicar elitismo
    tamaño_elite = config_ga['tamaño_elite']
    tamaño_poblacion = config_ga['tamaño_poblacion']
    
    # Seleccionar los mejores individuos de la población actual (élite)
    elite_indices = sorted(
        range(len(valores_fitness_actual)),
        key=lambda i: valores_fitness_actual[i]
    )[:tamaño_elite]
    
    elite_cromosomas = [poblacion_actual[i].clonar() for i in elite_indices]
    elite_fitness = [valores_fitness_actual[i] for i in elite_indices]
    
    # Combinar élite con los mejores hijos
    num_hijos_a_incluir = tamaño_poblacion - tamaño_elite
    
    if len(poblacion_hijos) >= num_hijos_a_incluir:
        # Seleccionar los mejores hijos
        hijos_indices = sorted(
            range(len(valores_fitness_hijos)),
            key=lambda i: valores_fitness_hijos[i]
        )[:num_hijos_a_incluir]
        
        mejores_hijos = [poblacion_hijos[i] for i in hijos_indices]
        fitness_mejores_hijos = [valores_fitness_hijos[i] for i in hijos_indices]
    else:
        # Si no hay suficientes hijos, usar todos y completar con élite adicional
        mejores_hijos = poblacion_hijos
        fitness_mejores_hijos = valores_fitness_hijos
        
        # Completar con más individuos de la élite si es necesario
        individuos_faltantes = num_hijos_a_incluir - len(poblacion_hijos)
        if individuos_faltantes > 0 and len(elite_cromosomas) > tamaño_elite:
            elite_adicional_indices = elite_indices[tamaño_elite:tamaño_elite + individuos_faltantes]
            for idx in elite_adicional_indices:
                mejores_hijos.append(poblacion_actual[idx].clonar())
                fitness_mejores_hijos.append(valores_fitness_actual[idx])
    
    # Combinar élite y mejores hijos
    nueva_poblacion = elite_cromosomas + mejores_hijos
    nuevos_valores_fitness = elite_fitness + fitness_mejores_hijos
    
    # Asegurar que el tamaño de la población sea correcto
    if len(nueva_poblacion) > tamaño_poblacion:
        nueva_poblacion = nueva_poblacion[:tamaño_poblacion]
        nuevos_valores_fitness = nuevos_valores_fitness[:tamaño_poblacion]
    
    return nueva_poblacion, nuevos_valores_fitness


def ejecutar_algoritmo_genetico_simple(
    piezas_requeridas_df: pd.DataFrame,
    barras_estandar_disponibles: List[Dict[str, Any]],
    desperdicios_reutilizables_previos: List[Dict[str, Any]],
    max_generaciones: int = 50,
    tamaño_poblacion: int = 30
) -> Cromosoma:
    """
    Versión simplificada del algoritmo genético con parámetros básicos.
    
    Args:
        piezas_requeridas_df: DataFrame con las piezas requeridas.
        barras_estandar_disponibles: Lista de barras estándar disponibles.
        desperdicios_reutilizables_previos: Lista de desperdicios reutilizables.
        max_generaciones: Número máximo de generaciones.
        tamaño_poblacion: Tamaño de la población.
    
    Returns:
        Cromosoma: Mejor cromosoma encontrado.
    """
    config_simple = {
        'tamaño_poblacion': tamaño_poblacion,
        'max_generaciones': max_generaciones,
        'estrategia_inicializacion': 'hibrida',
        'metodo_seleccion': 'torneo',
        'tamaño_torneo': 3,
        'tasa_cruce': 0.8,
        'estrategia_cruce': 'un_punto',
        'tasa_mutacion_individuo': 0.2,
        'tasa_mutacion_gen': 0.1,
        'elitismo': True,
        'tamaño_elite': 2,
        'criterio_convergencia': 'generaciones_sin_mejora',
        'generaciones_sin_mejora_max': 15,
        'tiempo_limite_segundos': 120,
        'logging_habilitado': True,
        'logging_frecuencia': 5
    }
    
    mejor_cromosoma, _ = ejecutar_algoritmo_genetico(
        piezas_requeridas_df,
        barras_estandar_disponibles,
        desperdicios_reutilizables_previos,
        config_simple
    )
    
    return mejor_cromosoma


def validar_configuracion_ga(config_ga: Dict[str, Any]) -> List[str]:
    """
    Valida la configuración del algoritmo genético.
    
    Args:
        config_ga: Configuración a validar.
    
    Returns:
        List[str]: Lista de errores encontrados (vacía si no hay errores).
    """
    errores = []
    
    # Validaciones básicas
    if config_ga.get('tamaño_poblacion', 0) < 2:
        errores.append("El tamaño de población debe ser al menos 2")
    
    if config_ga.get('max_generaciones', 0) < 1:
        errores.append("El número máximo de generaciones debe ser al menos 1")
    
    if not 0 <= config_ga.get('tasa_cruce', 0) <= 1:
        errores.append("La tasa de cruce debe estar entre 0 y 1")
    
    if not 0 <= config_ga.get('tasa_mutacion_individuo', 0) <= 1:
        errores.append("La tasa de mutación de individuo debe estar entre 0 y 1")
    
    if not 0 <= config_ga.get('tasa_mutacion_gen', 0) <= 1:
        errores.append("La tasa de mutación de gen debe estar entre 0 y 1")
    
    # Validaciones de elitismo
    if config_ga.get('elitismo', False):
        tamaño_elite = config_ga.get('tamaño_elite', 0)
        tamaño_poblacion = config_ga.get('tamaño_poblacion', 0)
        
        if tamaño_elite >= tamaño_poblacion:
            errores.append("El tamaño de la élite debe ser menor que el tamaño de la población")
        
        if tamaño_elite < 1:
            errores.append("El tamaño de la élite debe ser al menos 1 si el elitismo está habilitado")
    
    # Validaciones de métodos
    metodos_seleccion_validos = ['torneo', 'ruleta', 'elitista']
    if config_ga.get('metodo_seleccion') not in metodos_seleccion_validos:
        errores.append(f"Método de selección debe ser uno de: {metodos_seleccion_validos}")
    
    estrategias_cruce_validas = ['un_punto', 'dos_puntos', 'basado_en_piezas']
    if config_ga.get('estrategia_cruce') not in estrategias_cruce_validas:
        errores.append(f"Estrategia de cruce debe ser una de: {estrategias_cruce_validas}")
    
    return errores 
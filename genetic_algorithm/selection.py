"""
Módulo para la selección de padres en el algoritmo genético.

Este módulo implementa diferentes métodos de selección para elegir individuos
que participarán en la reproducción, basándose en su valor de fitness.
"""

import random
from typing import List, Tuple, Optional
import numpy as np

from .chromosome import Cromosoma


def validar_parametros_seleccion(
    poblacion: List[Cromosoma],
    valores_fitness: List[float],
    num_padres: int
) -> None:
    """
    Valida los parámetros de entrada para los métodos de selección.
    
    Args:
        poblacion: Lista de cromosomas de la población.
        valores_fitness: Lista de valores de fitness correspondientes.
        num_padres: Número de padres a seleccionar.
    
    Raises:
        ValueError: Si los parámetros no son válidos.
    """
    if len(poblacion) != len(valores_fitness):
        raise ValueError("La población y los valores de fitness deben tener la misma longitud")
    
    if num_padres <= 0:
        raise ValueError("El número de padres debe ser positivo")
    
    if num_padres > len(poblacion):
        raise ValueError("No se pueden seleccionar más padres que individuos en la población")
    
    if len(poblacion) == 0:
        raise ValueError("La población no puede estar vacía")


def seleccion_torneo(
    poblacion: List[Cromosoma],
    valores_fitness: List[float],
    num_padres: int,
    tamaño_torneo: int = 3
) -> List[Cromosoma]:
    """
    Selecciona padres usando el método de selección por torneo.
    
    En cada torneo, se seleccionan aleatoriamente 'tamaño_torneo' individuos
    y se elige el que tenga mejor fitness (menor valor).
    
    Args:
        poblacion: Lista de cromosomas de la población.
        valores_fitness: Lista de valores de fitness (menor es mejor).
        num_padres: Número de padres a seleccionar.
        tamaño_torneo: Número de individuos que participan en cada torneo.
    
    Returns:
        List[Cromosoma]: Lista de cromosomas seleccionados como padres.
    """
    validar_parametros_seleccion(poblacion, valores_fitness, num_padres)
    
    if tamaño_torneo <= 0:
        raise ValueError("El tamaño del torneo debe ser positivo")
    
    if tamaño_torneo > len(poblacion):
        tamaño_torneo = len(poblacion)
    
    padres_seleccionados = []
    
    for _ in range(num_padres):
        # Seleccionar aleatoriamente los participantes del torneo
        indices_torneo = random.sample(range(len(poblacion)), tamaño_torneo)
        
        # Encontrar el índice del mejor individuo en el torneo (menor fitness)
        mejor_indice = min(indices_torneo, key=lambda i: valores_fitness[i])
        
        # Añadir el ganador del torneo a la lista de padres
        padres_seleccionados.append(poblacion[mejor_indice])
    
    return padres_seleccionados


def seleccion_ruleta(
    poblacion: List[Cromosoma],
    valores_fitness: List[float],
    num_padres: int
) -> List[Cromosoma]:
    """
    Selecciona padres usando el método de selección por ruleta.
    
    La probabilidad de selección es inversamente proporcional al fitness
    (ya que menor fitness es mejor en nuestro problema).
    
    Args:
        poblacion: Lista de cromosomas de la población.
        valores_fitness: Lista de valores de fitness (menor es mejor).
        num_padres: Número de padres a seleccionar.
    
    Returns:
        List[Cromosoma]: Lista de cromosomas seleccionados como padres.
    """
    validar_parametros_seleccion(poblacion, valores_fitness, num_padres)
    
    # Convertir fitness a probabilidades (menor fitness = mayor probabilidad)
    # Primero, convertir a valores positivos si hay negativos
    fitness_array = np.array(valores_fitness)
    
    # Si todos los fitness son iguales, usar selección uniforme
    if np.all(fitness_array == fitness_array[0]):
        indices_seleccionados = random.choices(range(len(poblacion)), k=num_padres)
        return [poblacion[i] for i in indices_seleccionados]
    
    # Convertir fitness a valores de aptitud (mayor es mejor)
    # Usar transformación: aptitud = max_fitness - fitness + epsilon
    max_fitness = np.max(fitness_array)
    epsilon = 0.001  # Pequeño valor para evitar probabilidades cero
    aptitudes = max_fitness - fitness_array + epsilon
    
    # Asegurar que todas las aptitudes sean positivas
    if np.any(aptitudes <= 0):
        aptitudes = aptitudes - np.min(aptitudes) + epsilon
    
    # Calcular probabilidades
    suma_aptitudes = np.sum(aptitudes)
    probabilidades = aptitudes / suma_aptitudes
    
    # Seleccionar padres usando las probabilidades calculadas
    indices_seleccionados = np.random.choice(
        len(poblacion),
        size=num_padres,
        p=probabilidades,
        replace=True
    )
    
    return [poblacion[i] for i in indices_seleccionados]


def seleccion_elitista(
    poblacion: List[Cromosoma],
    valores_fitness: List[float],
    num_padres: int
) -> List[Cromosoma]:
    """
    Selecciona los mejores individuos de la población (elitismo).
    
    Args:
        poblacion: Lista de cromosomas de la población.
        valores_fitness: Lista de valores de fitness (menor es mejor).
        num_padres: Número de padres a seleccionar.
    
    Returns:
        List[Cromosoma]: Lista de los mejores cromosomas.
    """
    validar_parametros_seleccion(poblacion, valores_fitness, num_padres)
    
    # Crear pares (fitness, cromosoma) y ordenar por fitness
    pares_fitness_cromosoma = list(zip(valores_fitness, poblacion))
    pares_ordenados = sorted(pares_fitness_cromosoma, key=lambda x: x[0])
    
    # Seleccionar los mejores
    mejores_cromosomas = [cromosoma for _, cromosoma in pares_ordenados[:num_padres]]
    
    return mejores_cromosomas


def seleccionar_padres(
    poblacion: List[Cromosoma],
    valores_fitness: List[float],
    numero_de_padres_a_seleccionar: int,
    metodo_seleccion: str = 'torneo',
    tamaño_torneo: int = 3
) -> List[Cromosoma]:
    """
    Selecciona padres de la población usando el método especificado.
    
    Args:
        poblacion: Lista de cromosomas de la población.
        valores_fitness: Lista de valores de fitness correspondientes.
        numero_de_padres_a_seleccionar: Número de padres a seleccionar.
        metodo_seleccion: Método de selección ('torneo', 'ruleta', 'elitista').
        tamaño_torneo: Tamaño del torneo (solo para selección por torneo).
    
    Returns:
        List[Cromosoma]: Lista de cromosomas seleccionados como padres.
    
    Raises:
        ValueError: Si el método de selección no es reconocido.
    """
    if metodo_seleccion == 'torneo':
        return seleccion_torneo(
            poblacion,
            valores_fitness,
            numero_de_padres_a_seleccionar,
            tamaño_torneo
        )
    elif metodo_seleccion == 'ruleta':
        return seleccion_ruleta(
            poblacion,
            valores_fitness,
            numero_de_padres_a_seleccionar
        )
    elif metodo_seleccion == 'elitista':
        return seleccion_elitista(
            poblacion,
            valores_fitness,
            numero_de_padres_a_seleccionar
        )
    else:
        raise ValueError(f"Método de selección no reconocido: {metodo_seleccion}")


def seleccionar_parejas_para_cruce(
    padres: List[Cromosoma],
    metodo_emparejamiento: str = 'aleatorio'
) -> List[Tuple[Cromosoma, Cromosoma]]:
    """
    Forma parejas de padres para el cruce.
    
    Args:
        padres: Lista de cromosomas padres.
        metodo_emparejamiento: Método para formar parejas ('aleatorio', 'secuencial').
    
    Returns:
        List[Tuple[Cromosoma, Cromosoma]]: Lista de parejas de padres.
    """
    if len(padres) < 2:
        raise ValueError("Se necesitan al menos 2 padres para formar parejas")
    
    parejas = []
    
    if metodo_emparejamiento == 'aleatorio':
        # Mezclar la lista de padres y formar parejas consecutivas
        padres_mezclados = padres.copy()
        random.shuffle(padres_mezclados)
        
        for i in range(0, len(padres_mezclados) - 1, 2):
            parejas.append((padres_mezclados[i], padres_mezclados[i + 1]))
    
    elif metodo_emparejamiento == 'secuencial':
        # Formar parejas con individuos consecutivos
        for i in range(0, len(padres) - 1, 2):
            parejas.append((padres[i], padres[i + 1]))
    
    else:
        raise ValueError(f"Método de emparejamiento no reconocido: {metodo_emparejamiento}")
    
    return parejas


def calcular_presion_selectiva(
    valores_fitness: List[float],
    metodo_seleccion: str,
    tamaño_torneo: Optional[int] = None
) -> float:
    """
    Calcula una medida de la presión selectiva del método de selección.
    
    La presión selectiva indica qué tan fuertemente favorece el método
    a los individuos con mejor fitness.
    
    Args:
        valores_fitness: Lista de valores de fitness de la población.
        metodo_seleccion: Método de selección utilizado.
        tamaño_torneo: Tamaño del torneo (si aplica).
    
    Returns:
        float: Medida de presión selectiva (mayor valor = mayor presión).
    """
    if len(valores_fitness) == 0:
        return 0.0
    
    fitness_array = np.array(valores_fitness)
    
    if metodo_seleccion == 'torneo':
        # Para torneo, la presión aumenta con el tamaño del torneo
        if tamaño_torneo is None:
            tamaño_torneo = 3
        return tamaño_torneo / len(valores_fitness)
    
    elif metodo_seleccion == 'ruleta':
        # Para ruleta, calcular el coeficiente de variación
        if np.std(fitness_array) == 0:
            return 0.0
        return np.std(fitness_array) / np.mean(fitness_array)
    
    elif metodo_seleccion == 'elitista':
        # Elitismo tiene la máxima presión selectiva
        return 1.0
    
    else:
        return 0.0 
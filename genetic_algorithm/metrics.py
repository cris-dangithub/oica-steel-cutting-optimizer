"""
Módulo para métricas y monitoreo del algoritmo genético.

Este módulo proporciona herramientas para registrar, analizar y reportar
el progreso del algoritmo genético durante su ejecución.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
import statistics
import numpy as np

from .chromosome import Cromosoma


class RegistroEvolucion:
    """
    Clase para mantener un registro completo de la evolución del algoritmo genético.
    
    Registra estadísticas por generación y métricas globales para análisis posterior.
    """
    
    def __init__(self):
        """Inicializa un nuevo registro de evolución."""
        # Estadísticas por generación
        self.generaciones = []
        self.mejor_fitness_por_generacion = []
        self.fitness_promedio_por_generacion = []
        self.peor_fitness_por_generacion = []
        self.diversidad_por_generacion = []
        self.tiempo_por_generacion = []
        
        # Métricas globales
        self.mejor_fitness_global = float('inf')
        self.mejor_cromosoma_global = None
        self.generacion_mejor_global = 0
        self.tiempo_inicio = None
        self.tiempo_total = 0.0
        self.evaluaciones_fitness_total = 0
        
        # Configuración
        self.logging_habilitado = True
        self.logging_frecuencia = 10
    
    def iniciar_registro(self, config_ga: Optional[Dict[str, Any]] = None) -> None:
        """
        Inicia el registro de evolución.
        
        Args:
            config_ga: Configuración del algoritmo genético.
        """
        self.tiempo_inicio = time.time()
        
        if config_ga:
            self.logging_habilitado = config_ga.get('logging_habilitado', True)
            self.logging_frecuencia = config_ga.get('logging_frecuencia', 10)
    
    def registrar_generacion(
        self,
        generacion: int,
        poblacion: List[Cromosoma],
        valores_fitness: List[float],
        tiempo_generacion: float
    ) -> None:
        """
        Registra las estadísticas de una generación.
        
        Args:
            generacion: Número de la generación.
            poblacion: Población de cromosomas.
            valores_fitness: Valores de fitness correspondientes.
            tiempo_generacion: Tiempo que tomó procesar esta generación.
        """
        # Calcular estadísticas básicas
        mejor_fitness = min(valores_fitness)
        fitness_promedio = statistics.mean(valores_fitness)
        peor_fitness = max(valores_fitness)
        diversidad = calcular_diversidad_poblacion(poblacion, valores_fitness)
        
        # Registrar estadísticas
        self.generaciones.append(generacion)
        self.mejor_fitness_por_generacion.append(mejor_fitness)
        self.fitness_promedio_por_generacion.append(fitness_promedio)
        self.peor_fitness_por_generacion.append(peor_fitness)
        self.diversidad_por_generacion.append(diversidad)
        self.tiempo_por_generacion.append(tiempo_generacion)
        
        # Actualizar mejor global
        if mejor_fitness < self.mejor_fitness_global:
            self.mejor_fitness_global = mejor_fitness
            indice_mejor = valores_fitness.index(mejor_fitness)
            self.mejor_cromosoma_global = poblacion[indice_mejor].clonar()
            self.generacion_mejor_global = generacion
        
        # Actualizar contadores
        self.evaluaciones_fitness_total += len(valores_fitness)
        
        # Logging
        if self.logging_habilitado and generacion % self.logging_frecuencia == 0:
            self._log_generacion(generacion, mejor_fitness, fitness_promedio, diversidad)
    
    def finalizar_registro(self) -> None:
        """Finaliza el registro y calcula métricas finales."""
        if self.tiempo_inicio:
            self.tiempo_total = time.time() - self.tiempo_inicio
    
    def obtener_resumen(self) -> Dict[str, Any]:
        """
        Obtiene un resumen completo de la evolución.
        
        Returns:
            Dict con todas las métricas y estadísticas registradas.
        """
        return {
            'mejor_fitness_global': self.mejor_fitness_global,
            'generacion_mejor_global': self.generacion_mejor_global,
            'tiempo_total_segundos': self.tiempo_total,
            'evaluaciones_fitness_total': self.evaluaciones_fitness_total,
            'generaciones_ejecutadas': len(self.generaciones),
            'fitness_promedio_final': self.fitness_promedio_por_generacion[-1] if self.fitness_promedio_por_generacion else None,
            'diversidad_final': self.diversidad_por_generacion[-1] if self.diversidad_por_generacion else None,
            'mejora_total': (
                self.mejor_fitness_por_generacion[0] - self.mejor_fitness_global
                if self.mejor_fitness_por_generacion else 0
            ),
            'convergencia_detectada': self._detectar_convergencia_final()
        }
    
    def _log_generacion(
        self,
        generacion: int,
        mejor_fitness: float,
        fitness_promedio: float,
        diversidad: float
    ) -> None:
        """Imprime información de la generación actual."""
        print(f"Generación {generacion:3d} | "
              f"Mejor: {mejor_fitness:8.2f} | "
              f"Promedio: {fitness_promedio:8.2f} | "
              f"Diversidad: {diversidad:6.3f}")
    
    def _detectar_convergencia_final(self) -> bool:
        """Detecta si el algoritmo convergió al final de la ejecución."""
        if len(self.diversidad_por_generacion) < 10:
            return False
        
        # Considerar convergencia si la diversidad promedio de las últimas 10 generaciones es muy baja
        diversidad_reciente = self.diversidad_por_generacion[-10:]
        diversidad_promedio_reciente = statistics.mean(diversidad_reciente)
        
        return diversidad_promedio_reciente < 0.01


def calcular_diversidad_poblacion(
    poblacion: List[Cromosoma],
    valores_fitness: List[float]
) -> float:
    """
    Calcula la diversidad de una población basándose en la variación de fitness.
    
    Args:
        poblacion: Lista de cromosomas de la población.
        valores_fitness: Lista de valores de fitness correspondientes.
    
    Returns:
        float: Medida de diversidad (desviación estándar normalizada).
    """
    if len(valores_fitness) < 2:
        return 0.0
    
    # Calcular desviación estándar de los valores de fitness
    desviacion_estandar = statistics.stdev(valores_fitness)
    
    # Normalizar por el rango de fitness para obtener una medida relativa
    rango_fitness = max(valores_fitness) - min(valores_fitness)
    
    if rango_fitness == 0:
        return 0.0  # Población completamente homogénea
    
    diversidad_normalizada = desviacion_estandar / rango_fitness
    
    return diversidad_normalizada


def calcular_diversidad_estructural(poblacion: List[Cromosoma]) -> float:
    """
    Calcula la diversidad estructural de una población basándose en diferencias entre cromosomas.
    
    Args:
        poblacion: Lista de cromosomas de la población.
    
    Returns:
        float: Medida de diversidad estructural.
    """
    if len(poblacion) < 2:
        return 0.0
    
    diferencias_totales = 0.0
    comparaciones = 0
    
    for i in range(len(poblacion)):
        for j in range(i + 1, len(poblacion)):
            # Calcular diferencia entre cromosomas
            diferencia = _calcular_diferencia_cromosomas(poblacion[i], poblacion[j])
            diferencias_totales += diferencia
            comparaciones += 1
    
    return diferencias_totales / comparaciones if comparaciones > 0 else 0.0


def _calcular_diferencia_cromosomas(cromosoma1: Cromosoma, cromosoma2: Cromosoma) -> float:
    """
    Calcula una medida de diferencia entre dos cromosomas.
    
    Args:
        cromosoma1: Primer cromosoma.
        cromosoma2: Segundo cromosoma.
    
    Returns:
        float: Medida de diferencia.
    """
    # Diferencia en número de patrones
    diff_patrones = abs(len(cromosoma1.patrones) - len(cromosoma2.patrones))
    
    # Diferencia en desperdicio total
    diff_desperdicio = abs(
        cromosoma1.calcular_desperdicio_total() - 
        cromosoma2.calcular_desperdicio_total()
    )
    
    # Diferencia en número de barras estándar utilizadas
    diff_barras = abs(
        cromosoma1.contar_barras_estandar() - 
        cromosoma2.contar_barras_estandar()
    )
    
    # Combinar diferencias (pesos arbitrarios para normalización)
    diferencia_total = diff_patrones + diff_desperdicio * 0.1 + diff_barras
    
    return diferencia_total


def detectar_convergencia(
    historial_fitness: List[float],
    ventana_generaciones: int = 20,
    umbral_mejora: float = 0.001
) -> bool:
    """
    Detecta si el algoritmo ha convergido basándose en el historial de fitness.
    
    Args:
        historial_fitness: Lista de mejores fitness por generación.
        ventana_generaciones: Número de generaciones a considerar para convergencia.
        umbral_mejora: Mejora mínima requerida para no considerar convergencia.
    
    Returns:
        bool: True si se detecta convergencia, False en caso contrario.
    """
    if len(historial_fitness) < ventana_generaciones:
        return False
    
    # Obtener los últimos valores de fitness
    fitness_recientes = historial_fitness[-ventana_generaciones:]
    
    # Calcular la mejora en la ventana
    mejor_inicial = fitness_recientes[0]
    mejor_final = min(fitness_recientes)
    mejora = mejor_inicial - mejor_final
    
    # Considerar convergencia si la mejora es menor al umbral
    return mejora < umbral_mejora


def generar_reporte_evolucion(registro: RegistroEvolucion) -> str:
    """
    Genera un reporte textual detallado de la evolución.
    
    Args:
        registro: Registro de evolución a reportar.
    
    Returns:
        str: Reporte textual formateado.
    """
    resumen = registro.obtener_resumen()
    
    reporte = []
    reporte.append("=" * 60)
    reporte.append("REPORTE DE EVOLUCIÓN - ALGORITMO GENÉTICO")
    reporte.append("=" * 60)
    reporte.append("")
    
    # Métricas globales
    reporte.append("MÉTRICAS GLOBALES:")
    reporte.append(f"  Mejor fitness encontrado: {resumen['mejor_fitness_global']:.4f}")
    reporte.append(f"  Generación del mejor: {resumen['generacion_mejor_global']}")
    reporte.append(f"  Generaciones ejecutadas: {resumen['generaciones_ejecutadas']}")
    reporte.append(f"  Tiempo total: {resumen['tiempo_total_segundos']:.2f} segundos")
    reporte.append(f"  Evaluaciones de fitness: {resumen['evaluaciones_fitness_total']}")
    reporte.append("")
    
    # Métricas de convergencia
    reporte.append("ANÁLISIS DE CONVERGENCIA:")
    reporte.append(f"  Mejora total: {resumen['mejora_total']:.4f}")
    reporte.append(f"  Fitness promedio final: {resumen['fitness_promedio_final']:.4f}")
    reporte.append(f"  Diversidad final: {resumen['diversidad_final']:.4f}")
    reporte.append(f"  Convergencia detectada: {'Sí' if resumen['convergencia_detectada'] else 'No'}")
    reporte.append("")
    
    # Estadísticas de rendimiento
    if registro.tiempo_por_generacion:
        tiempo_promedio = statistics.mean(registro.tiempo_por_generacion)
        reporte.append("RENDIMIENTO:")
        reporte.append(f"  Tiempo promedio por generación: {tiempo_promedio:.3f} segundos")
        reporte.append(f"  Evaluaciones por segundo: {resumen['evaluaciones_fitness_total'] / resumen['tiempo_total_segundos']:.1f}")
        reporte.append("")
    
    # Evolución del fitness
    if len(registro.mejor_fitness_por_generacion) > 1:
        reporte.append("EVOLUCIÓN DEL FITNESS:")
        reporte.append(f"  Fitness inicial: {registro.mejor_fitness_por_generacion[0]:.4f}")
        reporte.append(f"  Fitness final: {registro.mejor_fitness_por_generacion[-1]:.4f}")
        
        # Mostrar algunas generaciones clave
        generaciones_clave = [0, len(registro.mejor_fitness_por_generacion) // 4, 
                             len(registro.mejor_fitness_por_generacion) // 2,
                             3 * len(registro.mejor_fitness_por_generacion) // 4,
                             len(registro.mejor_fitness_por_generacion) - 1]
        
        for gen_idx in generaciones_clave:
            if gen_idx < len(registro.mejor_fitness_por_generacion):
                gen = registro.generaciones[gen_idx]
                fitness = registro.mejor_fitness_por_generacion[gen_idx]
                reporte.append(f"    Generación {gen:3d}: {fitness:.4f}")
    
    reporte.append("")
    reporte.append("=" * 60)
    
    return "\n".join(reporte)


def exportar_metricas_csv(registro: RegistroEvolucion, archivo: str) -> None:
    """
    Exporta las métricas de evolución a un archivo CSV.
    
    Args:
        registro: Registro de evolución a exportar.
        archivo: Ruta del archivo CSV de destino.
    """
    import csv
    
    with open(archivo, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Escribir encabezados
        writer.writerow([
            'generacion',
            'mejor_fitness',
            'fitness_promedio',
            'peor_fitness',
            'diversidad',
            'tiempo_generacion'
        ])
        
        # Escribir datos
        for i in range(len(registro.generaciones)):
            writer.writerow([
                registro.generaciones[i],
                registro.mejor_fitness_por_generacion[i],
                registro.fitness_promedio_por_generacion[i],
                registro.peor_fitness_por_generacion[i],
                registro.diversidad_por_generacion[i],
                registro.tiempo_por_generacion[i]
            ]) 
# Plan de Implementación: Ciclo Evolutivo (Sección 4)

## Objetivo
Implementar el núcleo del algoritmo genético que orquesta todos los operadores previamente desarrollados en un ciclo evolutivo completo. Este módulo será el "motor" que ejecuta el proceso de optimización.

## Análisis del Requerimiento

El ciclo evolutivo debe:

1. **Orquestar el proceso completo**: Coordinar inicialización, evaluación, selección, cruce, mutación y reemplazo
2. **Gestionar criterios de parada**: Implementar múltiples condiciones para finalizar la evolución
3. **Mantener elitismo**: Preservar los mejores individuos entre generaciones
4. **Monitorear progreso**: Registrar métricas y estadísticas de evolución
5. **Ser configurable**: Permitir ajuste de parámetros sin modificar código

## Subtareas de Implementación

### Subtarea 4.1: Motor Principal del Algoritmo Genético
- **Archivo**: `ia-solution/genetic_algorithm/engine.py`
- **Función Principal**: `ejecutar_algoritmo_genetico(piezas_requeridas_df, barras_estandar_disponibles, desperdicios_reutilizables_previos, config_ga)`
- **Responsabilidades**:
  1. Inicializar población usando estrategias implementadas
  2. Evaluar fitness de toda la población
  3. Ejecutar bucle generacional:
     - Seleccionar padres
     - Aplicar cruce para generar descendencia
     - Aplicar mutación a la descendencia
     - Evaluar fitness de la nueva generación
     - Aplicar elitismo y reemplazo generacional
     - Verificar criterios de parada
  4. Retornar el mejor individuo encontrado y estadísticas

### Subtarea 4.2: Criterios de Parada
- **Archivo**: `ia-solution/genetic_algorithm/engine.py`
- **Función**: `verificar_criterios_parada(generacion_actual, mejor_fitness_historico, tiempo_inicio, config_ga)`
- **Criterios a Implementar**:
  1. **Número máximo de generaciones**: Límite absoluto de iteraciones
  2. **Convergencia por generaciones sin mejora**: Parar si no hay mejora en N generaciones
  3. **Tiempo límite**: Parar después de X segundos de ejecución
  4. **Fitness objetivo**: Parar si se alcanza un valor específico de fitness
  5. **Convergencia de población**: Parar si la diversidad es muy baja

### Subtarea 4.3: Elitismo y Reemplazo Generacional
- **Archivo**: `ia-solution/genetic_algorithm/engine.py`
- **Funciones**:
  - `aplicar_elitismo(poblacion_actual, poblacion_nueva, valores_fitness_actual, valores_fitness_nueva, tamaño_elite)`
  - `reemplazo_generacional(poblacion_padres, poblacion_hijos, estrategia_reemplazo)`
- **Estrategias de Reemplazo**:
  1. **Reemplazo completo**: La nueva generación reemplaza completamente a la anterior
  2. **Elitismo**: Los N mejores individuos se preservan automáticamente
  3. **Reemplazo steady-state**: Solo se reemplazan algunos individuos por generación

### Subtarea 4.4: Sistema de Métricas y Monitoreo
- **Archivo**: `ia-solution/genetic_algorithm/metrics.py`
- **Función Principal**: `RegistroEvolucion` (clase para mantener estadísticas)
- **Métricas a Registrar**:
  1. **Por generación**:
     - Mejor fitness de la generación
     - Fitness promedio de la población
     - Fitness del peor individuo
     - Diversidad de la población (desviación estándar de fitness)
     - Tiempo de ejecución de la generación
  2. **Globales**:
     - Mejor fitness histórico
     - Generación donde se encontró el mejor
     - Tiempo total de ejecución
     - Número total de evaluaciones de fitness
- **Funciones de Análisis**:
  - `calcular_diversidad_poblacion(poblacion, valores_fitness)`
  - `detectar_convergencia(historial_fitness, ventana_generaciones)`
  - `generar_reporte_evolucion(registro_evolucion)`

### Subtarea 4.5: Configuración y Parámetros
- **Archivo**: `ia-solution/genetic_algorithm/__init__.py` (actualizar)
- **Descripción**: Extender la configuración por defecto para incluir parámetros del ciclo evolutivo
- **Parámetros a Añadir**:
  ```python
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
  ```

### Subtarea 4.6: Tests del Ciclo Evolutivo
- **Archivo**: `ia-solution/tests/test_engine.py`
- **Tests a Implementar**:
  - Test de ejecución completa con datos pequeños
  - Test de criterios de parada individuales
  - Test de elitismo (verificar que mejores se preservan)
  - Test de convergencia con población homogénea
  - Test de configuraciones diferentes
  - Test de manejo de errores y casos límite

## Orden de Implementación Recomendado

1. **Métricas y Registro** (4.4) - Base para monitorear todo lo demás
2. **Motor Principal** (4.1) - Implementación básica del bucle
3. **Criterios de Parada** (4.2) - Condiciones para finalizar
4. **Elitismo** (4.3) - Preservación de mejores individuos
5. **Configuración** (4.5) - Parámetros y configuración flexible
6. **Tests** (4.6) - Validación de toda la funcionalidad

## Consideraciones de Implementación

### 1. Eficiencia Computacional
- El ciclo evolutivo será llamado frecuentemente, debe ser eficiente
- Considerar paralelización de evaluación de fitness para poblaciones grandes
- Implementar cache de fitness para cromosomas idénticos (opcional)

### 2. Robustez y Manejo de Errores
- Manejar casos donde la población converge prematuramente
- Validar que siempre hay individuos válidos en la población
- Implementar recuperación ante errores en operadores individuales

### 3. Flexibilidad y Configurabilidad
- Todos los parámetros deben ser configurables externamente
- Permitir diferentes estrategias de reemplazo y elitismo
- Facilitar la experimentación con diferentes configuraciones

### 4. Logging y Debugging
- Implementar logging detallado para facilitar debugging
- Permitir diferentes niveles de verbosidad
- Registrar información suficiente para análisis posterior

## Integración con Componentes Existentes

El motor del algoritmo genético utilizará:
- `population.inicializar_poblacion()` para crear la población inicial
- `fitness.calcular_fitness()` para evaluar individuos
- `selection.seleccionar_padres()` para elegir padres
- `crossover.cruzar()` para generar descendencia
- `mutation.mutar()` para introducir variaciones

## Resultado Esperado

Al completar esta sección, tendremos un algoritmo genético completamente funcional que:
- Puede resolver problemas de corte de acero de manera autónoma
- Proporciona control fino sobre el proceso evolutivo
- Genera estadísticas detalladas de la evolución
- Es robusto y maneja casos límite apropiadamente
- Está completamente validado con tests unitarios

Este será el núcleo que se integrará en el sistema principal en la Sección 5. 
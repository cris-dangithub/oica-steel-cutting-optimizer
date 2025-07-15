# Plan de Implementación: Operadores Genéticos (Sección 3)

## Objetivo
Implementar los operadores genéticos fundamentales del algoritmo genético: inicialización de población, selección, cruce y mutación. Estos operadores son responsables de crear, evolucionar y diversificar las soluciones candidatas.

## Análisis del Requerimiento

Los operadores genéticos constituyen el núcleo del algoritmo evolutivo y deben:

1. **Inicialización**: Crear una población inicial diversa y de calidad
2. **Selección**: Elegir individuos para reproducción basándose en su fitness
3. **Cruce**: Combinar características de dos padres para generar descendencia
4. **Mutación**: Introducir variaciones aleatorias para mantener diversidad

## Subtareas de Implementación

### Subtarea 3.1: Inicialización de la Población
- **Archivo**: `ia-solution/genetic_algorithm/population.py`
- **Función Principal**: `inicializar_poblacion(tamaño_poblacion, piezas_requeridas_df, barras_estandar_disponibles, desperdicios_reutilizables_previos, estrategia_inicializacion, config_ga)`
- **Estrategias a Implementar**:
  1. **Heurística**: Usar algoritmos constructivos como First Fit Decreasing (FFD) y Best Fit Decreasing (BFD)
  2. **Aleatoria con Reparación**: Generar soluciones aleatorias y repararlas para que sean válidas
  3. **Híbrida**: Combinar individuos heurísticos con aleatorios para balancear calidad y diversidad
- **Funciones Auxiliares**:
  - `generar_individuo_heuristico_ffd(piezas_requeridas_df, barras_disponibles, desperdicios_disponibles)`
  - `generar_individuo_heuristico_bfd(piezas_requeridas_df, barras_disponibles, desperdicios_disponibles)`
  - `generar_individuo_aleatorio_con_reparacion(piezas_requeridas_df, barras_disponibles, desperdicios_disponibles)`
  - `reparar_cromosoma(cromosoma, piezas_requeridas_df, barras_disponibles, desperdicios_disponibles)`

### Subtarea 3.2: Selección de Padres
- **Archivo**: `ia-solution/genetic_algorithm/selection.py`
- **Función Principal**: `seleccionar_padres(poblacion, valores_fitness, numero_de_padres_a_seleccionar, metodo_seleccion, tamaño_torneo)`
- **Métodos a Implementar**:
  1. **Selección por Torneo**: Método prioritario, robusto y eficiente
  2. **Selección por Ruleta**: Método opcional, proporcional al fitness
- **Funciones Auxiliares**:
  - `seleccion_torneo(poblacion, valores_fitness, num_padres, tamaño_torneo)`
  - `seleccion_ruleta(poblacion, valores_fitness, num_padres)` (opcional)
  - `validar_parametros_seleccion(poblacion, valores_fitness, num_padres)`

### Subtarea 3.3: Operador de Cruce
- **Archivo**: `ia-solution/genetic_algorithm/crossover.py`
- **Función Principal**: `cruzar(padre1_cromosoma, padre2_cromosoma, piezas_requeridas_df, tasa_cruce, estrategia_cruce, config_ga)`
- **Estrategias a Implementar**:
  1. **Cruce de Un Punto**: Dividir cromosomas en un punto y intercambiar segmentos
  2. **Cruce de Dos Puntos**: Dividir cromosomas en dos puntos e intercambiar segmento central
  3. **Cruce Basado en Piezas** (opcional): Intercambiar patrones que satisfacen piezas específicas
- **Funciones Auxiliares**:
  - `cruce_un_punto(padre1, padre2, piezas_requeridas_df)`
  - `cruce_dos_puntos(padre1, padre2, piezas_requeridas_df)`
  - `cruce_basado_en_piezas(padre1, padre2, piezas_requeridas_df)` (opcional)
  - `reparar_descendencia(hijo, piezas_requeridas_df, barras_disponibles, desperdicios_disponibles)`

### Subtarea 3.4: Operador de Mutación
- **Archivo**: `ia-solution/genetic_algorithm/mutation.py`
- **Función Principal**: `mutar(cromosoma, piezas_requeridas_df, barras_estandar_disponibles, desperdicios_reutilizables_previos, tasa_mutacion_individuo, tasa_mutacion_gen, config_ga)`
- **Operaciones de Mutación a Implementar**:
  1. **Cambiar Origen de Patrón**: Cambiar la barra origen de un patrón existente
  2. **Re-optimizar Patrón**: Reconstruir un patrón usando algoritmo heurístico
  3. **Mover Pieza entre Patrones**: Transferir una pieza de un patrón a otro
  4. **Añadir/Eliminar Pieza** (opcional): Ajustar la cantidad de piezas para equilibrar demanda
  5. **Dividir Patrón** (opcional): Separar un patrón en dos patrones más pequeños
  6. **Combinar Patrones** (opcional): Fusionar dos patrones en uno solo
- **Funciones Auxiliares**:
  - `mutacion_cambiar_origen_patron(cromosoma, indice_patron, nuevas_barras_disponibles)`
  - `mutacion_reoptimizar_patron(cromosoma, indice_patron, piezas_objetivo)`
  - `mutacion_mover_pieza(cromosoma, patron_origen, patron_destino, pieza_info)`
  - `mutacion_ajustar_cantidad_piezas(cromosoma, piezas_requeridas_df)` (opcional)
  - `mutacion_dividir_patron(cromosoma, indice_patron)` (opcional)
  - `mutacion_combinar_patrones(cromosoma, indice1, indice2)` (opcional)

### Subtarea 3.5: Tests Unitarios para Operadores
- **Archivo**: `ia-solution/tests/test_operators.py`
- **Tests a Implementar**:
  - Tests para inicialización de población (diversidad, validez)
  - Tests para selección (distribución, preservación de mejores)
  - Tests para cruce (validez de descendencia, herencia de características)
  - Tests para mutación (preservación de validez, introducción de variación)
- **Casos de Prueba Específicos**:
  - Población inicial con diferentes estrategias
  - Selección con diferentes tamaños de torneo
  - Cruce con cromosomas de diferentes tamaños
  - Mutación con diferentes tasas y operaciones

### Subtarea 3.6: Integración y Configuración
- **Archivo**: `ia-solution/genetic_algorithm/__init__.py` (actualizar)
- **Descripción**: Añadir configuraciones por defecto para los operadores genéticos
- **Configuraciones a Añadir**:
  ```python
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
      'operaciones_mutacion': ['cambiar_origen', 'reoptimizar', 'mover_pieza']
  }
  ```

## Dependencias y Prerrequisitos
- Las clases `Patron` y `Cromosoma` deben estar completamente implementadas ✅
- La función de fitness debe estar operativa ✅
- Las funciones utilitarias de cromosoma deben funcionar correctamente ✅
- Se necesita acceso a las barras estándar disponibles y desperdicios reutilizables

## Consideraciones de Implementación

### 1. Manejo de Validez de Cromosomas
- Todos los operadores deben garantizar que los cromosomas resultantes sean válidos
- Implementar funciones de reparación para corregir cromosomas inválidos
- Validar que se cumplan las restricciones de longitud de barras

### 2. Diversidad vs. Calidad
- La inicialización debe balancear soluciones de alta calidad con diversidad
- Los operadores de cruce y mutación deben preservar características buenas mientras exploran nuevas regiones

### 3. Eficiencia Computacional
- Los operadores serán llamados frecuentemente, por lo que deben ser eficientes
- Considerar el uso de estructuras de datos optimizadas para operaciones frecuentes
- Evitar copias innecesarias de cromosomas grandes

### 4. Parametrización Flexible
- Todos los operadores deben ser configurables mediante parámetros
- Permitir diferentes estrategias y tasas para adaptarse a diferentes problemas
- Facilitar la experimentación con diferentes configuraciones

## Orden de Implementación Recomendado
1. **Inicialización de Población** (3.1) - Base fundamental
2. **Selección** (3.2) - Necesaria para cruce
3. **Cruce** (3.3) - Operador principal de exploración
4. **Mutación** (3.4) - Operador de diversificación
5. **Tests Unitarios** (3.5) - Validación de todos los operadores
6. **Integración** (3.6) - Configuración y documentación final

## Siguiente Paso
Una vez completados los operadores genéticos, se procederá con la implementación del ciclo evolutivo (Sección 4) que orquestará todos estos operadores en el algoritmo principal. 
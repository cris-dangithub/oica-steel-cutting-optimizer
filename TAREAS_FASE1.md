# TAREAS DE IMPLEMENTACIÓN - FASE 1: ALGORITMO GENÉTICO

## Introducción

Este documento detalla las tareas específicas para implementar el Algoritmo Genético (AG), que constituye el núcleo de OICA. Estas tareas siguen la planificación establecida en `planification.txt` y consideran el estado actual documentado en `CHANGELOG_DESARROLLO.md`.

---

## 1. Diseño de la Representación del Individuo (Cromosoma)

### Tarea 1.1: Implementar la Estructura de Datos del Cromosoma ✅
- **Archivo a crear**: `ia-solution/genetic_algorithm/chromosome.py`
- **Descripción**: Crear las clases y estructuras para representar un cromosoma según la especificación
- **Entregables**:
  - Clase `Patron` con los atributos:
    - `origen_barra_longitud`: Longitud de la barra origen (float)
    - `origen_barra_tipo`: Tipo de barra ('estandar' o 'desperdicio')
    - `piezas_cortadas`: Lista de diccionarios con información de piezas
    - `desperdicio_patron_longitud`: Valor calculado del desperdicio (float)
    - `es_desperdicio_utilizable`: Booleano según `LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE`
  - Clase `Cromosoma` que contenga una lista de objetos `Patron`

### Tarea 1.2: Implementar Funciones Utilitarias para Cromosomas ✅
- **Archivo a crear**: `ia-solution/genetic_algorithm/chromosome_utils.py`
- **Descripción**: Desarrollar las funciones auxiliares para manipular y validar cromosomas
- **Entregables**:
  - `crear_patron_corte(origen_longitud, origen_tipo, lista_piezas_a_cortar_en_patron)`
  - `validar_patron(patron_dict, longitud_minima_desperdicio)`
  - `calcular_sumario_piezas_en_cromosoma(cromosoma)`
  - `validar_cromosoma_completitud(cromosoma, piezas_requeridas_df)`
  - `calcular_desperdicio_total_cromosoma(cromosoma)`
  - `obtener_nuevos_desperdicios_utilizables_de_cromosoma(cromosoma)`

### Tarea 1.3: Documentar la Estructura del Cromosoma ✅
- **Descripción**: Generar documentación completa con ejemplos
- **Entregables**:
  - Docstrings detallados en todas las clases y funciones
  - Type hints completos
  - Archivo `ia-solution/genetic_algorithm/README.md` con ejemplos de uso

---

## 2. Diseño de la Función de Fitness (Evaluación)

### Tarea 2.1: Implementar la Función de Fitness ✅
- **Archivo a crear**: `ia-solution/genetic_algorithm/fitness.py`
- **Descripción**: Implementar la función que evalúa la calidad de los cromosomas
- **Entregables**:
  - Función `calcular_fitness(cromosoma, piezas_requeridas_df, config_fitness)`
  - Funciones auxiliares para cálculos parciales:
    - `calcular_penalizacion_faltantes(sumario_piezas, piezas_requeridas_df, peso)`
    - `calcular_penalizacion_sobrantes(sumario_piezas, piezas_requeridas_df, peso)`
    - `calcular_penalizacion_barras_usadas(cromosoma, peso)`
    - `calcular_bonificacion_uso_desperdicios(cromosoma, peso)`

### Tarea 2.2: Desarrollar Tests para la Función de Fitness ✅
- **Archivo a crear**: `ia-solution/tests/test_fitness.py`
- **Descripción**: Crear casos de prueba completos para validar la función de fitness
- **Entregables**:
  - Test para cromosoma perfecto (cobertura completa, bajo desperdicio)
  - Test para cromosoma con piezas faltantes
  - Test para cromosoma con piezas sobrantes
  - Test para cromosoma con alto desperdicio pero demanda cubierta
  - Test para verificar el efecto de cambiar los pesos de los factores

---

## 3. Implementación de Operadores Genéticos

### Tarea 3.1: Implementar Inicialización de la Población
- **Archivo a crear**: `ia-solution/genetic_algorithm/population.py`
- **Descripción**: Desarrollar métodos para crear la población inicial
- **Entregables**:
  - Función `inicializar_poblacion(tamaño_poblacion, piezas_requeridas_df, barras_estandar_disponibles, desperdicios_reutilizables_previos, estrategia_inicializacion, config_ga)`
  - Implementación de las estrategias:
    - Heurística (First Fit Decreasing, Best Fit Decreasing)
    - Aleatoria con reparación
    - Híbrida

### Tarea 3.2: Implementar Selección de Padres
- **Archivo a crear**: `ia-solution/genetic_algorithm/selection.py`
- **Descripción**: Implementar los métodos de selección de individuos para reproducción
- **Entregables**:
  - Función `seleccionar_padres(poblacion, valores_fitness, numero_de_padres_a_seleccionar, metodo_seleccion, tamaño_torneo)`
  - Métodos de selección:
    - Torneo (implementación prioritaria)
    - Ruleta (opcional)

### Tarea 3.3: Implementar Operador de Cruce
- **Archivo a crear**: `ia-solution/genetic_algorithm/crossover.py`
- **Descripción**: Desarrollar métodos para combinar cromosomas padres y generar descendencia
- **Entregables**:
  - Función `cruzar(padre1_cromosoma, padre2_cromosoma, piezas_requeridas_df, tasa_cruce, estrategia_cruce, config_ga)`
  - Estrategias de cruce:
    - Un punto de patrones
    - Dos puntos de patrones
    - Cruce basado en piezas satisfechas (opcional avanzado)

### Tarea 3.4: Implementar Operador de Mutación
- **Archivo a crear**: `ia-solution/genetic_algorithm/mutation.py`
- **Descripción**: Desarrollar métodos para introducir variaciones aleatorias en los cromosomas
- **Entregables**:
  - Función `mutar(cromosoma, piezas_requeridas_df, barras_estandar_disponibles, desperdicios_reutilizables_previos, tasa_mutacion_individuo, tasa_mutacion_gen, config_ga)`
  - Operaciones de mutación:
    - Cambiar origen de un patrón
    - Re-optimizar un patrón
    - Mover una pieza entre patrones
    - Añadir/eliminar pieza para ajustar demanda (opcional)
    - Dividir un patrón (opcional)
    - Combinar dos patrones (opcional)

---

## 4. Ciclo Evolutivo y Criterios de Parada

### Tarea 4.1: Implementar el Bucle Principal del Algoritmo Genético
- **Archivo a crear**: `ia-solution/genetic_algorithm/engine.py`
- **Descripción**: Desarrollar el núcleo del algoritmo que orquesta todo el proceso evolutivo
- **Entregables**:
  - Función `ejecutar_algoritmo_genetico(piezas_requeridas_df, barras_estandar_disponibles, desperdicios_reutilizables_previos, config_ga)`
  - Implementación del bucle generacional completo
  - Sistema de registro de evolución (logging)

### Tarea 4.2: Implementar Criterios de Parada
- **Archivo a modificar**: `ia-solution/genetic_algorithm/engine.py`
- **Descripción**: Añadir condiciones para finalizar la evolución
- **Entregables**:
  - Implementación de criterios:
    - Número máximo de generaciones
    - Convergencia del fitness
    - Tiempo límite
    - Fitness objetivo alcanzado (opcional)

### Tarea 4.3: Implementar Elitismo
- **Archivo a modificar**: `ia-solution/genetic_algorithm/engine.py`
- **Descripción**: Garantizar que los mejores individuos se preserven entre generaciones
- **Entregables**:
  - Mecanismo para seleccionar los N mejores individuos
  - Función para transferirlos directamente a la siguiente generación

### Tarea 4.4: Implementar Sistema de Métricas de Evolución
- **Archivo a crear**: `ia-solution/genetic_algorithm/metrics.py`
- **Descripción**: Desarrollar funciones para monitorear el progreso del algoritmo
- **Entregables**:
  - Función para registrar estadísticas por generación:
    - Mejor fitness
    - Fitness promedio
    - Diversidad de la población
  - Generación opcional de gráficas de evolución

---

## 5. Integración en el Flujo Principal

### Tarea 5.1: Adaptar la Función de Optimización de Corte
- **Archivo a modificar**: `ia-solution/main.py`
- **Descripción**: Reemplazar el placeholder actual con el algoritmo genético implementado
- **Entregables**:
  - Nueva versión de `algoritmo_optimizacion_corte` que utilice el AG
  - Gestión adecuada de parámetros de configuración

### Tarea 5.2: Implementar Formato de Salida del AG
- **Archivo a crear**: `ia-solution/genetic_algorithm/output_formatter.py`
- **Descripción**: Convertir los resultados del AG al formato esperado por el script principal
- **Entregables**:
  - Función `formatear_salida_desde_cromosoma(mejor_cromosoma, longitud_minima_desperdicio)`
  - Conversión correcta entre estructuras de datos del AG y estructuras originales

### Tarea 5.3: Asegurar la Correcta Gestión de Desperdicios
- **Archivo a modificar**: `ia-solution/main.py`
- **Descripción**: Verificar que los desperdicios se gestionen correctamente entre ejecuciones
- **Entregables**:
  - Mejoras en el código de gestión de desperdicios entre grupos de ejecución
  - Pruebas de integración para verificar el funcionamiento correcto

---

## Consideraciones de Implementación

### Estructura de Archivos
```
ia-solution/
├── genetic_algorithm/
│   ├── __init__.py
│   ├── chromosome.py
│   ├── chromosome_utils.py
│   ├── fitness.py
│   ├── population.py
│   ├── selection.py
│   ├── crossover.py
│   ├── mutation.py
│   ├── engine.py
│   ├── metrics.py
│   ├── output_formatter.py
│   └── README.md
├── tests/
│   ├── __init__.py
│   ├── test_chromosome.py
│   ├── test_fitness.py
│   ├── test_operators.py
│   └── test_engine.py
├── main.py
└── utils/
    └── visualization.py (opcional)
```

### Priorización de Tareas
1. Representación del Cromosoma (1.1, 1.2) ✅
2. Función de Fitness (2.1, 2.2) ✅
3. Inicialización de Población (3.1)
4. Operadores Básicos (3.2, 3.3, 3.4)
5. Bucle Principal (4.1, 4.2, 4.3)
6. Integración (5.1, 5.2, 5.3)
7. Testing y Documentación (1.3, 2.2) ✅

### Dependencias entre Tareas
- La implementación del Cromosoma (1.1, 1.2) es prerrequisito para todas las demás tareas ✅
- La Función de Fitness (2.1) es prerrequisito para los Operadores (3.x) y el Ciclo Evolutivo (4.x) ✅
- La Integración (5.x) requiere que todas las demás tareas estén completadas 
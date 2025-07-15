# Plan de Implementación: Función de Fitness (Sección 1.2)

## Objetivo
Implementar una función de fitness robusta que evalúe la calidad de las soluciones (cromosomas) generadas por el algoritmo genético, considerando múltiples factores como el desperdicio, la cobertura de la demanda y otros criterios relevantes.

## Análisis del Requerimiento

Según `planification.txt`, la función de fitness debe:

1. Evaluar la calidad de un cromosoma, con el objetivo principal de minimizar el desperdicio total.
2. Considerar penalizaciones por:
   - Piezas faltantes (no cumplir con la demanda)
   - Piezas sobrantes (producir más de lo necesario)
   - Uso excesivo de barras estándar (opcional)
3. Considerar bonificaciones por:
   - Uso eficiente de desperdicios previos (opcional)
4. Retornar un valor único (menor es mejor) que se utilizará para guiar la evolución.

## Subtareas de Implementación

### Subtarea 1: Implementación de la Función Principal de Fitness
- **Archivo**: `ia-solution/genetic_algorithm/fitness.py`
- **Función**: `calcular_fitness(cromosoma, piezas_requeridas_df, config_fitness)`
- **Descripción**: Implementar la función central que combina todos los factores de evaluación.
- **Parámetros**:
  - `cromosoma`: Un objeto de tipo `Cromosoma` a evaluar.
  - `piezas_requeridas_df`: DataFrame con las piezas requeridas (columnas: id_pedido, longitud_pieza_requerida, cantidad_requerida).
  - `config_fitness`: Diccionario con los pesos de las penalizaciones/bonificaciones (ej: `{'peso_desperdicio': 1.0, 'penalizacion_faltantes': 1000.0, ...}`).
- **Retorno**: Un valor float (menor es mejor).

### Subtarea 2: Implementación de Funciones Auxiliares para Cálculos Parciales
- **Archivo**: `ia-solution/genetic_algorithm/fitness.py`
- **Funciones**:
  - `calcular_penalizacion_faltantes(sumario_piezas, piezas_requeridas_df, peso)`
  - `calcular_penalizacion_sobrantes(sumario_piezas, piezas_requeridas_df, peso)`
  - `calcular_penalizacion_barras_usadas(cromosoma, peso)`
  - `calcular_bonificacion_uso_desperdicios(cromosoma, peso)`
- **Descripción**: Implementar funciones específicas para cada componente del cálculo de fitness, facilitando su testing y mantenimiento.

### Subtarea 3: Configuración por Defecto y Normalización
- **Archivo**: `ia-solution/genetic_algorithm/fitness.py`
- **Función**: `obtener_config_fitness_default()`
- **Descripción**: Proporcionar una configuración por defecto para los pesos de los distintos factores.
- **Consideraciones**: 
  - Los pesos deben calibrarse para que las penalizaciones por no cumplir la demanda sean mucho más altas que el desperdicio.
  - Valores recomendados: `penalizacion_faltantes > penalizacion_sobrantes > peso_desperdicio`.

### Subtarea 4: Implementación de Tests Unitarios
- **Archivo**: `ia-solution/tests/test_fitness.py`
- **Tests a implementar**:
  - Test para un cromosoma perfecto (cubre demanda, bajo desperdicio)
  - Test para un cromosoma con piezas faltantes
  - Test para un cromosoma con piezas sobrantes
  - Test para un cromosoma con alto desperdicio pero demanda cubierta
  - Test para verificar el efecto de cambiar los pesos de los factores
- **Descripción**: Crear tests exhaustivos que validen que la función de fitness refleja correctamente la calidad de las soluciones.

### Subtarea 5: Integración Inicial con el Módulo de Cromosoma
- **Descripción**: Asegurar que la función de fitness interactúa correctamente con las estructuras de cromosoma existentes.
- **Consideraciones**:
  - Usar `chromosome_utils.calcular_sumario_piezas_en_cromosoma` para obtener el sumario de piezas.
  - Validar el manejo correcto de los diferentes tipos de valores en los campos de `piezas_requeridas_df`.

### Subtarea 6: Documentación y Ejemplos de Uso
- **Archivo**: `ia-solution/genetic_algorithm/README.md` (actualizar)
- **Descripción**: Agregar sección sobre la función de fitness con ejemplos de uso.

## Dependencias y Prerrequisitos
- Las clases `Patron` y `Cromosoma` deben estar completamente implementadas (Sección 1.1).
- La función `calcular_sumario_piezas_en_cromosoma` debe funcionar correctamente.
- Se debe contar con un entorno de pruebas para ejecutar los tests unitarios.

## Siguiente Paso
Una vez completada la función de fitness, se procederá con la implementación de los operadores genéticos (Sección 1.3). 
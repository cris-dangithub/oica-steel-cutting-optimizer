# Optimizador Inteligente de Cortes de Acero (OICA)

## 1. Descripción del Proyecto

El Optimizador Inteligente de Cortes de Acero (OICA) es un proyecto enfocado en resolver el problema de optimización del corte de barras de acero en entornos de construcción o metalmecánica. El objetivo principal es minimizar el desperdicio de material, lo cual se traduce en una reducción de costos y un impacto ambiental positivo.

**Problema a Solucionar:**
En la industria, se requiere cortar barras de acero de longitudes estándar (ej. 6m, 9m, 12m) para obtener una lista de piezas de longitudes específicas y en cantidades determinadas (cartilla de acero). Este proceso, si no se optimiza, puede generar un desperdicio considerable de material. La complejidad aumenta debido a:
* **Compatibilidad de Diámetros:** Las barras tienen diferentes diámetros (ej. #3, #4, #5). Los desperdicios generados de una barra de un diámetro específico solo pueden ser reutilizados para cortar otras piezas del mismo diámetro.
* **Secuencia de Ejecución en Obra:** Los pedidos de piezas se agrupan según el momento en que se necesitarán en la obra (grupos de ejecución). Es crucial respetar esta secuencia: los desperdicios generados por un grupo de ejecución temprano (ej. Grupo 1) pueden ser utilizados por grupos posteriores (Grupo 2, 3,...), pero no a la inversa. Esto asegura que no se utilicen prematuramente materiales destinados a fases futuras del proyecto.

**Solución Propuesta:**
Este proyecto propone el desarrollo de una solución basada en Inteligencia Artificial (IA), específicamente utilizando **Algoritmos Genéticos (AG)**, para generar patrones de corte óptimos. Los AG son metaheurísticas robustas, capaces de explorar eficientemente espacios de solución complejos y encontrar soluciones de alta calidad (cercanas al óptimo global) para problemas de optimización combinatoria como el "cutting stock problem" (CSP) o problema de corte de material.

## 2. Estado Actual del Proyecto

El proyecto se encuentra en una fase inicial de desarrollo, con una estructura base funcional implementada en Python.

* **Código Base:** El script principal `optimizador_cortes.py` (a ser creado o que ya existe parcialmente) contiene:
    * Funciones para cargar datos de entrada:
        * `cartilla_acero.csv`: Lista de piezas requeridas con sus longitudes, cantidades, número de barra (diámetro) y grupo de ejecución.
        * `barras_estandar.json`: Longitudes de las barras nuevas disponibles por cada número de barra.
    * Lógica para procesar los pedidos de forma jerárquica:
        1.  Agrupación por `numero_barra` (diámetro).
        2.  Dentro de cada `numero_barra`, procesamiento secuencial por `grupo_ejecucion`.
    * Manejo básico de desperdicios: Los desperdicios generados en un grupo de ejecución se consideran disponibles para los grupos subsecuentes del mismo `numero_barra`.
    * Un **placeholder** para la función `algoritmo_optimizacion_corte`, que es donde se implementará el Algoritmo Genético. Actualmente, este placeholder utiliza una heurística muy simple (similar a First Fit Decreasing) y no representa una optimización real.
* **Archivos de Ejemplo:** Se incluyen `cartilla_acero.csv` y `barras_estandar.json` para pruebas iniciales.
* **Salida:** El script genera un archivo `resultados_optimizacion_cortes.csv` con los patrones de corte (simulados por el placeholder) y un resumen de los desperdicios.

## 3. Archivos del Proyecto

* `optimizador_cortes.py`: Script principal de Python que contiene la lógica de la aplicación.
* `cartilla_acero.csv`: Archivo CSV de ejemplo que contiene los pedidos de piezas de acero.
    * Columnas: `id_pedido`, `numero_barra`, `longitud_pieza_requerida`, `cantidad_requerida`, `grupo_ejecucion`.
* `barras_estandar.json`: Archivo JSON de ejemplo que define las longitudes de las barras estándar disponibles para cada tipo de barra.
    * Formato: `{"#numero_barra": [longitud1, longitud2], ...}`
* `README.md`: Este archivo, proporcionando una guía completa del proyecto.
* `resultados_optimizacion_cortes.csv` (generado): Archivo CSV con los resultados de la optimización.

## 4. Requisitos Previos

* Python 3.7 o superior.
* Biblioteca `pandas`: Para la manipulación de datos.
    ```bash
    pip install pandas
    ```

## 5. Instrucciones de Uso (Estado Actual)

1.  **Preparar Archivos de Entrada:**
    * Asegúrate de que los archivos `cartilla_acero.csv` y `barras_estandar.json` estén presentes en el mismo directorio que `optimizador_cortes.py`, o modifica las rutas en las constantes `RUTA_CARTILLA_ACERO` y `RUTA_BARRAS_ESTANDAR` dentro del script.
    * Modifica estos archivos con tus datos reales si es necesario, siguiendo el formato especificado.
2.  **Ejecutar el Script:**
    ```bash
    python optimizador_cortes.py
    ```
3.  **Revisar Resultados:**
    * Se imprimirá un resumen en la consola.
    * Se generará (o sobrescribirá) el archivo `resultados_optimizacion_cortes.csv` con los patrones de corte detallados. **Nota:** Con el placeholder actual, estos patrones no son óptimos.

## 6. Roadmap de Desarrollo (Plan a Futuro Detallado)

Para transformar el actual placeholder en una solución de IA robusta y exitosa, se propone el siguiente roadmap:

### Fase 1: Implementación del Algoritmo Genético (Núcleo de la IA)

Esta fase es crucial y se centrará en reemplazar el placeholder `algoritmo_optimizacion_corte` con una implementación completa de un Algoritmo Genético.

* **1.1. Diseño de la Representación del Individuo (Cromosoma):**
    * **Concepto:** Un individuo (cromosoma) en el AG representará una solución completa para un subproblema específico: el conjunto de patrones de corte necesarios para satisfacer la demanda de piezas de un `numero_barra` y `grupo_ejecucion` particular, utilizando las `barras_estandar_disponibles_para_tipo` y los `desperdicios_reutilizables_previos`.
    * **Estructura Detallada:** Un cromosoma podría ser una lista de "patrones de corte". Cada "patrón de corte" es, a su vez, un diccionario que especifica:
        1.  `origen_barra_longitud`: La longitud de la barra de origen (una barra estándar o un desperdicio reutilizable).
        2.  `piezas_cortadas`: Una lista de diccionarios, donde cada diccionario representa una pieza cortada e incluye `id_pedido` y `longitud`.
        3.  `desperdicio_patron`: El desperdicio generado por este patrón específico.
    * **Ejemplo de Cromosoma (conceptual):**
        ```python
        cromosoma = [
            {'origen_barra_longitud': 12.0, 
             'piezas_cortadas': [{'id_pedido': 101, 'longitud': 2.75}, {'id_pedido': 101, 'longitud': 2.75}, ...],
             'desperdicio_patron': 0.5
            },
            {'origen_barra_longitud': 6.0,  
             'piezas_cortadas': [{'id_pedido': 102, 'longitud': 2.1}, ...],
             'desperdicio_patron': 0.3
            },
            # ... más patrones
        ]
        ```
    * **Consideraciones:** La representación debe ser flexible para manejar diferentes longitudes de barras de origen y debe facilitar la evaluación (cálculo de desperdicio y piezas cubiertas). Cada cromosoma debe intentar cubrir todas las `piezas_requeridas_df` para el subproblema actual.

* **1.2. Diseño de la Función de Fitness (Evaluación):**
    * **Objetivo Principal:** La función de fitness evaluará la "calidad" de un cromosoma (solución). El objetivo primordial es **minimizar el desperdicio total** generado por el conjunto de patrones en el cromosoma.
    * **Cálculo del Desperdicio Total del Cromosoma:** Sumar `desperdicio_patron` de todos los patrones en el cromosoma.
    * **Penalizaciones (Cruciales para guiar la evolución):**
        * **Incumplimiento de la Demanda:** Aplicar una penalización severa si el conjunto de patrones de corte en el cromosoma no satisface la cantidad requerida de cada tipo de pieza (identificada por `id_pedido` y `longitud_pieza_requerida`). La penalización debe ser proporcional a la cantidad de piezas faltantes y su longitud total.
        * **(Opcional) Uso Excesivo de Barras Estándar:** Si se usan muchas barras estándar cuando se podrían haber usado menos (o más desperdicios), se podría aplicar una penalización menor.
    * **Valoración Positiva (Opcional):**
        * Se podría dar un pequeño "bono" por utilizar eficientemente los `desperdicios_reutilizables_previos`.
    * **Normalización:** El valor de fitness debe ser consistente (ej. un menor valor de fitness es mejor si se está minimizando el desperdicio).
    * **Manejo de `LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE`:** Los `desperdicio_patron` por debajo de este umbral se consideran pérdida total. Los que están por encima pueden ser reutilizados y deben contabilizarse como `nuevos_desperdicios_utilizables` al final de la ejecución del AG para un subproblema.

* **1.3. Implementación de Operadores Genéticos:**
    * **1.3.1. Inicialización de la Población:**
        * **Estrategia:** Generar una población inicial de N cromosomas.
        * **Métodos:**
            * **Aleatoria (Con Reparación):** Generar patrones de corte aleatoriamente. Esto es complejo de hacer bien para que cubra la demanda. Podría ser más factible generar un conjunto de patrones que *intentan* cubrir la demanda y luego "repararlos" o penalizarlos fuertemente si no lo hacen.
            * **Heurística:** Utilizar heurísticas simples como *First Fit Decreasing (FFD)* o *Best Fit Decreasing (BFD)* para generar cada individuo de la población inicial. Cada individuo (cromosoma) sería el resultado de aplicar la heurística a la lista completa de `piezas_requeridas_df` para el subproblema actual, usando las `barras_estandar_disponibles_para_tipo` y `desperdicios_reutilizables_previos`. Esto proporciona un punto de partida de mayor calidad.
    * **1.3.2. Selección:**
        * **Propósito:** Elegir individuos "padres" de la población actual para crear la siguiente generación. Los individuos con mejor fitness (menor desperdicio y penalizaciones) tienen mayor probabilidad de ser seleccionados.
        * **Métodos Comunes:** Selección por Torneo, Selección por Ruleta. La Selección por Torneo es robusta y fácil de implementar.
    * **1.3.3. Cruce (Crossover):**
        * **Propósito:** Combinar la información genética de dos padres para crear descendencia.
        * **Diseño Específico para el Problema:**
            * **Cruce a Nivel de Patrones:** Intercambiar subconjuntos de patrones de corte entre dos cromosomas padres. Por ejemplo, tomar los primeros `m` patrones del Padre1 y los restantes del Padre2.
            * **Cruce Basado en Piezas Satisfechas:** Identificar un subconjunto de piezas requeridas. Un hijo hereda los patrones que satisfacen estas piezas de un padre, y los patrones que satisfacen las piezas restantes del otro padre.
        * **Manejo de Validez y Reparación:** El cruce puede generar hijos inválidos (ej. que no cubren toda la demanda o cubren piezas de más). Se necesitarán mecanismos de reparación (ej. aplicar una heurística para completar cortes faltantes o eliminar cortes redundantes) o una fuerte penalización en la función de fitness.
        * **Tasa de Cruce (`Pc`):** Probabilidad de que dos padres seleccionados se crucen.
    * **1.3.4. Mutación:**
        * **Propósito:** Introducir variabilidad genética.
        * **Diseño Específico para el Problema:**
            * **Cambiar Origen de un Patrón:** Para un patrón de corte, intentar usar una barra de origen diferente (otra estándar o un desperdicio disponible) si las piezas caben.
            * **Reorganizar Piezas en un Patrón:** Intentar un empaquetamiento diferente de las mismas piezas en una barra de origen para ver si reduce el desperdicio de ese patrón (más relevante para 2D, pero podría tener efectos menores en 1D si se combina con otras mutaciones).
            * **Mover Pieza entre Patrones:** Mover una pieza de un patrón de corte a otro, si hay espacio y mejora la solución global.
            * **Aplicar una Heurística Local:** Tomar un subconjunto de piezas de un cromosoma y re-optimizar sus patrones usando una heurística rápida.
        * **Tasa de Mutación (`Pm`):** Probabilidad de que un cromosoma mute. Suele ser una probabilidad baja.

* **1.4. Ciclo Evolutivo y Criterios de Parada:**
    * **Flujo del AG:**
        1.  Inicializar población.
        2.  Evaluar fitness de cada individuo.
        3.  Bucle (hasta criterio de parada):
            a.  Seleccionar padres.
            b.  Aplicar cruce para generar descendencia.
            c.  Aplicar mutación a la descendencia.
            d.  Evaluar fitness de la nueva descendencia.
            e.  Reemplazar la población antigua con la nueva (estrategias: elitismo - siempre mantener al mejor individuo, reemplazo generacional completo, etc.).
    * **Criterios de Parada:** Número máximo de generaciones, convergencia del fitness, tiempo límite.

* **1.5. Integración en `algoritmo_optimizacion_corte`:**
    * La función `algoritmo_optimizacion_corte` recibirá `piezas_requeridas_df`, `barras_estandar_disponibles_para_tipo`, y `desperdicios_reutilizables_previos`.
    * Dentro de esta función, se ejecutará el AG completo.
    * Devolverá la mejor solución encontrada (el cromosoma con el mejor fitness) formateada como `patrones_de_corte_generados` (lista de diccionarios como se describió para la salida del placeholder) y la lista de `nuevos_desperdicios_utilizables`.

### Fase 2: Refinamiento y Optimización del Algoritmo

* **2.1. Ajuste de Parámetros del AG (Hyperparameter Tuning):**
    * Parámetros: Tamaño de población, tasas de cruce/mutación, tipo de selección, etc.
    * Estrategias: Experimentación, Grid Search, Random Search.
* **2.2. Optimización del Rendimiento Computacional:**
    * Profiling para identificar cuellos de botella.
    * Uso eficiente de NumPy, memoization, posible paralelización.
* **2.3. Manejo Avanzado de Desperdicios:**
    * Estrategias más inteligentes para seleccionar y priorizar desperdicios reutilizables.
    * Inventario de desperdicios más estructurado (ej. con cantidades).

### Fase 3: Mejoras de Usabilidad y Funcionalidades Adicionales

* **3.1. Interfaz de Usuario:**
    * CLI Mejorada (ej. con `Typer` o `Click`).
    * (Opcional) GUI simple (ej. con `Streamlit` o `Tkinter`).
* **3.2. Visualización de Resultados:**
    * Gráficos de patrones de corte (ej. con `matplotlib`).
    * Reportes más detallados.
* **3.3. Configuración Flexible:**
    * Permitir modificar parámetros clave (`LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE`, parámetros del AG) vía archivo de configuración (JSON, INI).
* **3.4. Consideraciones de Restricciones Adicionales:**
    * **Kerf del Corte (Ancho de la Cuchilla):** Si el proceso de corte consume material.
    * **Número Máximo de Cortes por Barra.**
    * **Optimización Multi-Objetivo** (ej. minimizar desperdicio Y minimizar número de barras usadas).

### Fase 4: Pruebas Exhaustivas y Validación

* **4.1. Creación de un Conjunto de Datos de Prueba Extenso:**
    * Múltiples `cartilla_acero.csv` con diversos escenarios.
* **4.2. Comparación con Otros Métodos/Software (Benchmarking):**
    * Implementar heurísticas simples (FFD, BFD) y comparar.
    * Comparar con software existente si es posible.
* **4.3. Validación con Usuarios/Expertos del Dominio:**
    * Obtener feedback de ingenieros, personal de obra, etc.

### Fase 5: Documentación y Mantenimiento

* **5.1. Documentación Completa del Código:** Docstrings, comentarios.
* **5.2. Manual de Usuario Detallado.**
* **5.3. Plan de Mantenimiento y Futuras Actualizaciones.**

## 7. Prompt para Continuar en IDE (Cursor, VSCode con IA)

```text
Eres un asistente de IA experto en Python y algoritmos de optimización, específicamente Algoritmos Genéticos. Estoy trabajando en un proyecto llamado "Optimizador Inteligente de Cortes de Acero (OICA)". El código base actual (`optimizador_cortes.py`) carga los datos de los pedidos (piezas requeridas de acero) y las longitudes de las barras estándar disponibles. También tiene una estructura para procesar los pedidos jerárquicamente: primero por tipo de barra (diámetro, `numero_barra`) y luego secuencialmente por grupo de ejecución (orden de uso en obra, `grupo_ejecucion`).

La función clave que necesitamos desarrollar es `algoritmo_optimizacion_corte(piezas_requeridas_df, barras_estandar_disponibles_para_tipo, desperdicios_reutilizables_previos, config_algoritmo=None)`. Actualmente, esta función es solo un placeholder que usa una heurística muy simple.

Mi objetivo principal es implementar un Algoritmo Genético robusto dentro de esta función para resolver el problema de corte 1D (similar al "cutting stock problem" o "bin packing problem" con variaciones específicas como el manejo secuencial de desperdicios).

Necesito tu ayuda para avanzar con la **Fase 1 del roadmap: Implementación del Algoritmo Genético**. Específicamente, vamos a empezar por los puntos 1.1 y 1.2 del README:

1.  **Diseñar la representación del individuo (cromosoma)** (Sección 1.1 del README):
    * Un individuo (cromosoma) debe representar una solución completa para un subproblema: el conjunto de patrones de corte para satisfacer las `piezas_requeridas_df` (DataFrame con columnas 'id_pedido', 'longitud_pieza_requerida', 'cantidad_requerida'), utilizando las `barras_estandar_disponibles_para_tipo` (lista de floats) y los `desperdicios_reutilizables_previos` (lista de floats).
    * Detalla la estructura de datos en Python para un cromosoma. Un cromosoma será una lista de patrones. Cada patrón (un diccionario) debe especificar:
        * `'origen_barra_longitud'`: float (longitud de la barra estándar o desperdicio usado).
        * `'piezas_cortadas'`: lista de diccionarios, cada uno con `'id_pedido'` y `'longitud'`.
        * `'desperdicio_patron'`: float.
    * Proporciona un ejemplo de cómo se vería una instancia de un cromosoma en Python.

2.  **Diseñar la función de fitness inicial** (Sección 1.2 del README):
    * La función de fitness tomará un cromosoma (como se definió arriba) y las `piezas_requeridas_df` originales como entrada.
    * Debe calcular el desperdicio total del cromosoma.
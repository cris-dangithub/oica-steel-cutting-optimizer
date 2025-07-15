# Plan de Acción Detallado y Resolutivo para OICA (Optimizador Inteligente de Cortes de Acero)

## Preámbulo: Filosofía del Plan

Este plan se ha elaborado con un énfasis en la **resolución proactiva de problemas** y la **investigación aplicada**. Cada tarea incluye no solo *qué* hacer, sino también *cómo* se podría abordar, posibles desafíos y consideraciones para asegurar el éxito. El objetivo es que este documento sirva como una hoja de ruta viva y detallada para el desarrollo del proyecto OICA.

---

## **Fase 1: Implementación del Algoritmo Genético (Núcleo de la IA)**

Esta es la fase más crítica. El éxito aquí determinará la viabilidad de la solución.

### **1.1. Diseño de la Representación del Individuo (Cromosoma)**

Un cromosoma representa una solución candidata para un subproblema (un `numero_barra` y `grupo_ejecucion` específicos).

*   **Tarea 1.1.1: Definir Estructura de Datos del Cromosoma en Python.**
    *   **Resolución:**
        *   **Cromosoma:** Será una `list` de "patrones de corte".
        *   **Patrón de Corte:** Un `dict` con las siguientes claves:
            *   `'origen_barra_longitud'`: `float`. Longitud de la barra de origen (estándar o desperdicio).
            *   `'origen_barra_tipo'`: `str`. Puede ser `'estandar'` o `'desperdicio'`. Útil para trazabilidad y estrategias.
            *   `'piezas_cortadas'`: `list` de `dict`. Cada `dict` representa una pieza cortada:
                *   `'id_pedido'`: `any` (tipo del `id_pedido` en la cartilla).
                *   `'longitud_pieza'`: `float`.
                *   `'cantidad_pieza_en_patron'`: `int` (normalmente 1, pero podría ser >1 si se cortan múltiples piezas idénticas de un mismo pedido en el mismo patrón).
            *   `'desperdicio_patron_longitud'`: `float`. Longitud del sobrante de este patrón específico. Calculado como `origen_barra_longitud - sum(longitud_pieza * cantidad_pieza_en_patron para cada pieza en piezas_cortadas)`.
            *   `'es_desperdicio_utilizable'`: `bool`. `True` si `desperdicio_patron_longitud >= LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE`.
    *   **Investigación/Consideraciones:**
        *   Evaluar si añadir un `'id_patron'` único a cada patrón dentro del cromosoma puede ser útil para operadores genéticos más complejos o para el análisis de resultados.
        *   La `cantidad_pieza_en_patron` es importante si se considera que una pieza de un pedido puede repetirse en el mismo patrón. Generalmente, para CSP 1D, se lista cada corte. Si un pedido requiere 3 piezas de 2m, y un patrón las incluye, `piezas_cortadas` contendría 3 entradas para ese `id_pedido` con `longitud_pieza=2.0`.

*   **Tarea 1.1.2: Crear Funciones Utilitarias para la Gestión de Cromosomas.**
    *   **`crear_patron_corte(origen_longitud, origen_tipo, lista_piezas_a_cortar_en_patron)`:**
        *   Calcula el desperdicio y determina si es utilizable. Retorna el diccionario del patrón.
    *   **`validar_patron(patron_dict, longitud_minima_desperdicio)`:**
        *   Verifica que la suma de piezas no exceda `origen_barra_longitud`.
        *   Verifica el cálculo de `desperdicio_patron_longitud` y `es_desperdicio_utilizable`.
    *   **`calcular_sumario_piezas_en_cromosoma(cromosoma)`:**
        *   Entrada: Un cromosoma.
        *   Salida: Un `dict` o `pd.Series` que resume cuántas piezas de cada `(id_pedido, longitud_pieza_requerida)` se han cubierto en total por el cromosoma. Esto es vital para la función de fitness. Ejemplo: `{ (101, 2.5): 5, (102, 3.1): 2 }`.
    *   **`validar_cromosoma_completitud(cromosoma, piezas_requeridas_df)`:**
        *   Usa `calcular_sumario_piezas_en_cromosoma` para verificar si el cromosoma satisface *exactamente* la demanda en `piezas_requeridas_df` (ni más ni menos piezas de cada tipo).
    *   **`calcular_desperdicio_total_cromosoma(cromosoma)`:**
        *   Suma `desperdicio_patron_longitud` de todos los patrones en el cromosoma.
    *   **`obtener_nuevos_desperdicios_utilizables_de_cromosoma(cromosoma)`:**
        *   Retorna una lista de `desperdicio_patron_longitud` para aquellos patrones donde `es_desperdicio_utilizable` es `True`.

*   **Tarea 1.1.3: Documentar y Ejemplificar la Estructura del Cromosoma.**
    *   **Resolución:** Usar docstrings detallados y type hints en Python.
    *   **Ejemplo:**
        ```python
        # Ejemplo de 'piezas_requeridas_df' (para un subproblema)
        # id_pedido | longitud_pieza_requerida | cantidad_requerida
        # -------------------------------------------------------
        # P001      | 2.5                      | 2
        # P002      | 1.0                      | 3

        # Ejemplo de cromosoma
        cromosoma_ejemplo = [
            {
                'origen_barra_longitud': 6.0,
                'origen_barra_tipo': 'estandar',
                'piezas_cortadas': [
                    {'id_pedido': 'P001', 'longitud_pieza': 2.5, 'cantidad_pieza_en_patron': 1},
                    {'id_pedido': 'P001', 'longitud_pieza': 2.5, 'cantidad_pieza_en_patron': 1},
                    {'id_pedido': 'P002', 'longitud_pieza': 1.0, 'cantidad_pieza_en_patron': 1}
                ],
                'desperdicio_patron_longitud': 0.0, # 6.0 - (2.5 + 2.5 + 1.0)
                'es_desperdicio_utilizable': False # Asumiendo LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE = 0.5
            },
            {
                'origen_barra_longitud': 3.0, # Supongamos que es un desperdicio previo
                'origen_barra_tipo': 'desperdicio',
                'piezas_cortadas': [
                    {'id_pedido': 'P002', 'longitud_pieza': 1.0, 'cantidad_pieza_en_patron': 1},
                    {'id_pedido': 'P002', 'longitud_pieza': 1.0, 'cantidad_pieza_en_patron': 1}
                ],
                'desperdicio_patron_longitud': 1.0, # 3.0 - (1.0 + 1.0)
                'es_desperdicio_utilizable': True
            }
        ]
        ```

### **1.2. Diseño de la Función de Fitness (Evaluación)**

La función de fitness es el corazón del AG. Debe guiar la evolución hacia soluciones óptimas.

*   **Tarea 1.2.1: Implementar la Función de Fitness `calcular_fitness(cromosoma, piezas_requeridas_df, config_fitness)`**.
    *   **Entradas:**
        *   `cromosoma`: El individuo a evaluar.
        *   `piezas_requeridas_df`: El DataFrame original con `id_pedido`, `longitud_pieza_requerida`, `cantidad_requerida` para el subproblema actual.
        *   `config_fitness`: Un `dict` con los pesos de las penalizaciones/bonificaciones.
            *   Ej: `{'peso_desperdicio': 1.0, 'penalizacion_faltantes': 1000.0, 'penalizacion_sobrantes': 500.0, ...}`
    *   **Cálculos Internos:**
        1.  **Sumario de Piezas Cortadas:** Usar `calcular_sumario_piezas_en_cromosoma(cromosoma)`.
        2.  **Cálculo de Piezas Faltantes y Sobrantes:**
            *   Iterar sobre `piezas_requeridas_df`. Para cada `(id_pedido, longitud_pieza_requerida)`:
                *   `cantidad_cortada = sumario_piezas_cortadas.get((id_pedido, longitud_pieza_requerida), 0)`
                *   `cantidad_faltante = max(0, fila['cantidad_requerida'] - cantidad_cortada)`
                *   `cantidad_sobrante = max(0, cantidad_cortada - fila['cantidad_requerida'])`
            *   `valor_penalizacion_faltantes = sum(cantidad_faltante * longitud_pieza_requerida) * config_fitness['penalizacion_faltantes']`
            *   `valor_penalizacion_sobrantes = sum(cantidad_sobrante * longitud_pieza_requerida) * config_fitness['penalizacion_sobrantes']`
        3.  **Cálculo del Desperdicio Total:** `desperdicio_total = calcular_desperdicio_total_cromosoma(cromosoma) * config_fitness['peso_desperdicio']`.
        4.  **(Opcional) Penalización por Número de Barras Usadas:**
            *   Contar el número de patrones que usan `'origen_barra_tipo': 'estandar'`.
            *   `penalizacion_num_barras = num_barras_estandar_usadas * config_fitness.get('penalizacion_num_barras_estandar', 0.0)`
        5.  **(Opcional) Bonificación por Uso de Desperdicios Previos:**
            *   Contar la longitud total de desperdicios previos utilizados como `origen_barra_longitud`.
            *   `bonificacion_uso_desperdicios = total_long_desperdicios_usados * config_fitness.get('bonificacion_uso_desperdicios', 0.0)`
    *   **Salida:** `float`. El valor de fitness. **Menor es mejor.**
        *   `fitness = desperdicio_total + valor_penalizacion_faltantes + valor_penalizacion_sobrantes + penalizacion_num_barras - bonificacion_uso_desperdicios`
    *   **Investigación/Consideraciones:**
        *   La magnitud de los factores de penalización es crítica. Deben ser lo suficientemente altos para que el AG priorice satisfacer la demanda sobre minimizar el desperdicio si la demanda no está cubierta.
        *   Normalización del fitness: Considerar si es necesario, aunque para selección por torneo no es estrictamente indispensable.

*   **Tarea 1.2.2: Testear Rigurosamente la Función de Fitness.**
    *   **Resolución:** Crear casos de prueba unitarios:
        *   Cromosoma perfecto (cubre demanda, bajo desperdicio).
        *   Cromosoma con piezas faltantes.
        *   Cromosoma con piezas sobrantes.
        *   Cromosoma con alto desperdicio pero demanda cubierta.
        *   Cromosoma usando solo barras estándar vs. uno usando desperdicios.
    *   Verificar que los valores de fitness reflejen la calidad esperada.

### **1.3. Implementación de Operadores Genéticos**

Estos operadores impulsan la evolución de la población.

*   **Tarea 1.3.1: Inicialización de la Población.**
    *   **`inicializar_poblacion(tamaño_poblacion, piezas_requeridas_df, barras_estandar_disponibles, desperdicios_reutilizables_previos, estrategia_inicializacion='heuristica', config_ga)`**
    *   **Estrategias:**
        *   **`'heuristica'` (Recomendada para un buen inicio):**
            *   Para cada individuo a generar:
                1.  Tomar una copia de `piezas_requeridas_df`.
                2.  Crear una lista de barras disponibles (estándar + desperdicios previos, quizás ordenadas).
                3.  Aplicar una heurística como First Fit Decreasing (FFD) o Best Fit Decreasing (BFD):
                    *   Ordenar las piezas requeridas (decreciente por longitud para FFD/BFD).
                    *   Iterar sobre las piezas. Para cada pieza, intentar colocarla en la primera/mejor barra disponible (estándar o desperdicio) donde quepa.
                    *   Si se llena una barra o no caben más piezas, se cierra el patrón y se toma otra barra.
                    *   Continuar hasta que todas las piezas requeridas estén asignadas a patrones.
                4.  El conjunto de patrones generados forma un cromosoma.
            *   Esto tiende a generar individuos iniciales ya válidos (demandas cubiertas) y relativamente buenos.
        *   **`'aleatoria_con_reparacion'` (Más exploratoria pero compleja):**
            *   Generar patrones de corte aleatoriamente (seleccionar una barra de origen al azar, seleccionar piezas al azar que quepan) hasta que la demanda se cubra.
            *   Necesitará un mecanismo de "reparación" para asegurar que la demanda se cumpla, o dependerá fuertemente de la función de fitness para penalizar individuos inválidos.
        *   **`'hibrida'`:** Generar una parte de la población con heurísticas y otra parte más aleatoriamente para diversidad.
    *   **Investigación/Consideraciones:**
        *   Las heurísticas FFD/BFD son un buen punto de partida. Investigar variantes específicas para CSP.
        *   La calidad de la población inicial puede impactar significativamente la velocidad de convergencia y la calidad de la solución final.

*   **Tarea 1.3.2: Selección de Padres.**
    *   **`seleccionar_padres(poblacion, valores_fitness, numero_de_padres_a_seleccionar, metodo_seleccion='torneo', tamaño_torneo=3)`**
    *   **Métodos:**
        *   **`'torneo'` (Robusta y comúnmente usada):**
            1.  Para cada padre a seleccionar:
            2.  Elegir `tamaño_torneo` individuos al azar de la `poblacion`.
            3.  El individuo con el mejor `valor_fitness` (menor) de este grupo es seleccionado como padre.
            4.  Permitir que un individuo pueda ser seleccionado múltiples veces (selección con reemplazo del torneo).
        *   **`'ruleta'` (Fitness Proportionate Selection):**
            *   Requiere que los fitness sean positivos y que un mayor fitness sea mejor. Se necesitaría una transformación: `prob_seleccion_i = (1 / (1 + fitness_i)) / sum(1 / (1 + fitness_j) para todo j)`.
            *   Es más sensible a grandes diferencias en los valores de fitness. El torneo suele ser más estable.
    *   **Investigación/Consideraciones:** El tamaño del torneo (`k`) es un parámetro a ajustar. Valores comunes son 2-5.

*   **Tarea 1.3.3: Cruce (Crossover).**
    *   **`cruzar(padre1_cromosoma, padre2_cromosoma, piezas_requeridas_df, tasa_cruce, estrategia_cruce='un_punto_patrones', config_ga)`**
    *   Se aplica con una probabilidad `tasa_cruce`. Si no se aplica, los hijos son clones de los padres.
    *   **Estrategias (específicas para esta representación):**
        *   **`'un_punto_patrones'`:**
            1.  Elegir un punto de cruce aleatorio a lo largo de la lista de patrones de `padre1` y `padre2`.
            2.  `hijo1 = padre1.patrones[0:punto] + padre2.patrones[punto:]`
            3.  `hijo2 = padre2.patrones[0:punto] + padre1.patrones[punto:]`
        *   **`'dos_puntos_patrones'`:** Similar, pero se eligen dos puntos y se intercambia el segmento central de patrones.
        *   **`'cruce_basado_en_piezas_satisfechas'` (Más complejo):**
            1.  Seleccionar un subconjunto aleatorio de `id_pedido` de `piezas_requeridas_df`.
            2.  Hijo1 toma de Padre1 los patrones que satisfacen principalmente esos `id_pedido` y de Padre2 los patrones para el resto. (Requiere lógica para identificar qué patrones sirven a qué pedidos).
    *   **Manejo de Validez Post-Cruce:**
        *   Los hijos generados pueden ser inválidos (no cubrir la demanda, o cubrirla en exceso, o tener patrones redundantes).
        *   **Opción 1 (Preferida inicialmente):** Confiar en la función de fitness para penalizar fuertemente a los hijos inválidos. Ellos probablemente no sobrevivirán.
        *   **Opción 2 (Más avanzada):** Implementar una función `reparar_cromosoma(cromosoma, piezas_requeridas_df, ...)` que intente ajustar el hijo para que sea válido (ej., añadiendo patrones para piezas faltantes usando una heurística, o eliminando patrones redundantes). Esto puede ser costoso computacionalmente.
    *   **Investigación/Consideraciones:** El diseño del operador de cruce es crucial. Debe permitir la combinación efectiva de "bloques de construcción" (buenos patrones o conjuntos de patrones) de los padres.

*   **Tarea 1.3.4: Mutación.**
    *   **`mutar(cromosoma, piezas_requeridas_df, barras_estandar_disponibles, desperdicios_reutilizables_previos, tasa_mutacion_individuo, tasa_mutacion_gen, config_ga)`**
    *   Se aplica a un individuo con `tasa_mutacion_individuo`. Si se selecciona para mutar, se pueden aplicar una o más operaciones de mutación a sus "genes" (patrones o piezas dentro de patrones) con `tasa_mutacion_gen` (o una probabilidad fija por operación).
    *   **Operaciones de Mutación Específicas:**
        1.  **Cambiar Origen de un Patrón:**
            *   Seleccionar un patrón al azar. Intentar cambiar su `origen_barra_longitud` a otra barra estándar disponible o a un desperdicio utilizable, siempre que todas sus `piezas_cortadas` aún quepan. Priorizar si el nuevo origen reduce el `desperdicio_patron_longitud`.
        2.  **Re-Optimizar un Patrón (Local Search Ligero):**
            *   Tomar las `piezas_cortadas` de un patrón. Intentar re-empaquetarlas en su `origen_barra_longitud` usando una heurística simple (ej., FFD solo para esas piezas en esa barra) para ver si se reduce el `desperdicio_patron_longitud`.
        3.  **Mover una Pieza entre Patrones:**
            *   Seleccionar una pieza de un patrón A. Intentar moverla a otro patrón B si hay espacio. Actualizar desperdicios. Esto puede requerir dividir un patrón o crear uno nuevo si no cabe.
        4.  **Añadir/Eliminar Pieza para Ajustar Demanda (si se permite que la mutación repare):**
            *   Si tras el cruce faltan piezas, una mutación podría intentar añadir un patrón simple para una pieza faltante.
            *   Si sobran, eliminar una pieza de un patrón.
        5.  **Dividir un Patrón:** Si un patrón usa una barra grande y tiene un desperdicio considerable, intentar dividirlo en dos patrones usando barras de origen más pequeñas si es posible para las piezas contenidas.
        6.  **Combinar dos Patrones:** Si dos patrones usan barras pequeñas y juntos podrían caber en una barra más grande de forma más eficiente.
    *   **Manejo de Validez Post-Mutación:** Similar al cruce, confiar en la función de fitness o implementar mecanismos de reparación. Las mutaciones deberían, idealmente, ser pequeñas perturbaciones.
    *   **Investigación/Consideraciones:** La tasa de mutación suele ser baja (ej. 1-10% para `tasa_mutacion_individuo`). Un conjunto diverso de operadores de mutación puede ayudar a escapar de óptimos locales.

### **1.4. Ciclo Evolutivo y Criterios de Parada**

Aquí se orquesta el proceso generacional.

*   **Tarea 1.4.1: Implementar el Bucle Principal del Algoritmo Genético.**
    ```python
    # En la función algoritmo_optimizacion_corte(...)
    poblacion = inicializar_poblacion(...)
    mejor_cromosoma_global = None
    mejor_fitness_global = float('inf')

    for generacion_actual in range(config_ga['max_generaciones']):
        valores_fitness = [calcular_fitness(ind, piezas_requeridas_df, config_ga['fitness_config']) for ind in poblacion]

        # Actualizar mejor solución global
        for i, fitness_ind in enumerate(valores_fitness):
            if fitness_ind < mejor_fitness_global:
                mejor_fitness_global = fitness_ind
                mejor_cromosoma_global = deepcopy(poblacion[i]) # Guardar una copia profunda

        # (Opcional) Logging: print(f"Generación {generacion_actual}: Mejor Fitness = {mejor_fitness_global}")

        # Selección de Elites (si se usa)
        elites = []
        if config_ga.get('num_elites', 0) > 0:
            indices_ordenados_por_fitness = sorted(range(len(poblacion)), key=lambda k: valores_fitness[k])
            for i in range(config_ga['num_elites']):
                elites.append(deepcopy(poblacion[indices_ordenados_por_fitness[i]]))
        
        nueva_poblacion = elites[:] # Iniciar con elites

        # Generar el resto de la nueva población
        while len(nueva_poblacion) < config_ga['tamaño_poblacion']:
            padre1, padre2 = seleccionar_padres(poblacion, valores_fitness, 2, config_ga['seleccion_config'])
            
            hijo1, hijo2 = deepcopy(padre1), deepcopy(padre2) # Empezar como clones

            if random.random() < config_ga['tasa_cruce']:
                # El cruce puede modificar hijo1, hijo2 directamente o retornar nuevos
                hijo1, hijo2 = cruzar(padre1, padre2, piezas_requeridas_df, config_ga['tasa_cruce'], config_ga['cruce_config']) 
            
            mutar(hijo1, ...) # Mutación puede modificar el hijo directamente
            mutar(hijo2, ...)

            nueva_poblacion.append(hijo1)
            if len(nueva_poblacion) < config_ga['tamaño_poblacion']: # Asegurar no exceder tamaño
                nueva_poblacion.append(hijo2)
        
        poblacion = nueva_poblacion

        # Comprobar Criterios de Parada Adicionales (ej. convergencia)
        # if condicion_convergencia_cumplida or tiempo_limite_excedido:
        #     break
    
    return formatear_salida_desde_cromosoma(mejor_cromosoma_global, LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE)
    ```

*   **Tarea 1.4.2: Implementar Criterios de Parada.**
    *   **Número Máximo de Generaciones:** (`config_ga['max_generaciones']`). Simple y común.
    *   **Convergencia del Fitness:** Si el `mejor_fitness_global` no mejora (o mejora menos de un `epsilon`) durante `N` generaciones consecutivas.
    *   **Tiempo Límite:** Detener si el AG excede un tiempo de ejecución máximo.
    *   **Fitness Objetivo Alcanzado:** Si se conoce un valor de fitness óptimo o aceptable (raro para CSP complejos).

*   **Tarea 1.4.3: (Opcional pero Recomendado) Implementar Elitismo.**
    *   Asegura que los mejores `N` individuos de una generación pasen directamente a la siguiente sin modificaciones. Ayuda a no perder buenas soluciones encontradas. (Incluido en el esqueleto del bucle arriba).

*   **Tarea 1.4.4: Registrar Métricas de Evolución.**
    *   Guardar/imprimir el mejor fitness y el fitness promedio de la población en cada generación. Útil para analizar la convergencia y para el ajuste de parámetros.

### **1.5. Integración en `algoritmo_optimizacion_corte`**

*   **Tarea 1.5.1: Adaptar la Firma de la Función y el Flujo.**
    *   La función `algoritmo_optimizacion_corte` recibirá `piezas_requeridas_df`, `barras_estandar_disponibles_para_tipo`, `desperdicios_reutilizables_previos`, y un `config_algoritmo` (que contendrá `config_ga`, `LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE`, etc.).
    *   Dentro, se inicializarán los parámetros del AG y se ejecutará el ciclo evolutivo.

*   **Tarea 1.5.2: Formatear la Salida del AG.**
    *   **`formatear_salida_desde_cromosoma(mejor_cromosoma, longitud_minima_desperdicio)`:**
        *   Toma el `mejor_cromosoma_global` encontrado.
        *   Convierte su lista de patrones al formato esperado por el script principal:
            *   `patrones_de_corte_generados`: Lista de diccionarios como se definió en el `main.py` original (Ej: `[{'barra_origen_longitud': L, 'cortes_realizados': [c1, c2], ...}]`). Se necesita una traducción de la representación del cromosoma a esta.
            *   `nuevos_desperdicios_utilizables`: Lista de longitudes de desperdicios (`desperdicio_patron_longitud`) del `mejor_cromosoma` que sean `es_desperdicio_utilizable == True`.

*   **Tarea 1.5.3: Asegurar la Correcta Interacción con el Flujo Principal del Script.**
    *   Verificar que los desperdicios se pasen y actualicen correctamente entre llamadas secuenciales a `algoritmo_optimizacion_corte` para diferentes grupos de ejecución.

---

## **Fase 2: Refinamiento y Optimización del Algoritmo**

Una vez que el AG básico funciona, se busca mejorar su rendimiento y la calidad de las soluciones.

### **2.1. Ajuste de Parámetros del AG (Hyperparameter Tuning)**

*   **Parámetros Clave a Ajustar:**
    *   `tamaño_poblacion`
    *   `max_generaciones`
    *   `tasa_cruce`
    *   `tasa_mutacion_individuo` (y/o específicas de cada operador de mutación)
    *   `tamaño_torneo` (si se usa selección por torneo)
    *   `num_elites`
    *   Pesos en la función de fitness (`config_fitness`).
*   **Estrategias de Ajuste:**
    *   **Manual/Empírica:** Probar valores comunes de la literatura, observar el comportamiento de convergencia (gráficas de fitness vs generación) y ajustar un parámetro a la vez.
    *   **Grid Search:** Definir un rango y pasos para cada parámetro y probar todas las combinaciones (muy costoso).
    *   **Random Search:** Definir un rango/distribución para cada parámetro y probar combinaciones aleatorias (más eficiente que Grid Search).
    *   **Herramientas Automatizadas (Ej: Optuna, Hyperopt, KerasTuner si se adaptara):** Estas bibliotecas pueden automatizar la búsqueda del mejor conjunto de hiperparámetros. Requieren definir una función objetivo que ejecute el AG con un conjunto de parámetros y devuelva una métrica (ej., mejor fitness promedio sobre varias corridas).
*   **Metodología:**
    1.  Definir un conjunto de problemas de prueba representativos.
    2.  Para cada conjunto de hiperparámetros, ejecutar el AG múltiples veces (ej. 5-10) en cada problema de prueba para promediar resultados (debido a la naturaleza estocástica del AG).
    3.  La métrica a optimizar podría ser el mejor fitness promedio o la tasa de éxito en encontrar soluciones de cierta calidad.

### **2.2. Optimización del Rendimiento Computacional**

*   **Profiling:**
    *   Usar `cProfile` y `snakeviz` (o `pyinstrument`) para identificar las funciones más lentas. Probablemente serán la función de fitness y los operadores genéticos si involucran mucha creación/copia de objetos o bucles profundos.
*   **Técnicas de Optimización:**
    *   **Vectorización (NumPy/Pandas):** Donde sea posible, usar operaciones vectorizadas en lugar de bucles Python explícitos, especialmente en cálculos sobre `piezas_requeridas_df` o al analizar cromosomas.
    *   **Reducir Creación de Objetos:** La creación y copia (especialmente `deepcopy`) de muchos objetos en cada generación puede ser costosa. Evaluar si se pueden modificar objetos "in-place" (con cuidado) o usar copias superficiales donde sea seguro.
    *   **Memoization/Caching:** Si la función de fitness se llama múltiples veces con el mismo cromosoma (ej. elites no modificadas), se podría cachear su resultado.
    *   **Uso Eficiente de Estructuras de Datos:** Asegurar que se usan las estructuras adecuadas (ej. `set` para búsquedas rápidas de pertenencia si es necesario).
    *   **Paralelización (con `multiprocessing`):**
        *   La evaluación del fitness de los individuos de una población es altamente paralizable. Cada individuo puede ser evaluado en un proceso separado.
        *   Considerar el overhead de la comunicación entre procesos. Puede no ser beneficioso para poblaciones muy pequeñas o funciones de fitness muy rápidas.

### **2.3. Manejo Avanzado de Desperdicios (Dentro y Fuera del AG)**

*   **Estrategias de Selección de Desperdicios para el AG:**
    *   Cuando un cromosoma necesita una barra de origen y puede usar un desperdicio, ¿cuál elegir?
        *   **Best Fit para Desperdicios:** Elegir el desperdicio reutilizable que, al ser usado, minimice el nuevo desperdicio generado por ese patrón.
        *   **First Fit para Desperdicios:** Usar el primer desperdicio encontrado que sea suficientemente grande.
        *   Se puede incorporar esta lógica en los operadores de inicialización y mutación.
*   **Inventario de Desperdicios Más Estructurado (para el sistema global):**
    *   En lugar de una simple lista de longitudes en `desperdicios_globales_por_tipo_barra`, podría ser una lista de diccionarios `{'longitud': L, 'cantidad': Q, 'origen_grupo_ejecucion': G}`.
    *   Esto permite un seguimiento más fino y podría influir en la estrategia de uso (ej. priorizar desperdicios más antiguos o de ciertos grupos).
*   **Consolidación de Desperdicios (Post-procesamiento):**
    *   Una vez que todos los grupos de un `numero_barra` han sido procesados, analizar los `desperdicios_globales_por_tipo_barra` finales. ¿Se pueden "virtualmente" cortar y unir algunos de estos desperdicios para formar piezas más grandes y útiles que podrían ser consideradas como nuevas "barras de desperdicio" para un futuro ciclo de planificación? (Esto es más una optimización del inventario que del AG en sí).

---

## **Fase 3: Mejoras de Usabilidad y Funcionalidades Adicionales**

Hacer el sistema más usable y potente.

### **3.1. Interfaz de Usuario (UI)**

*   **CLI Mejorada (con `Typer` o `Click`):**
    *   Argumentos claros para archivos de entrada (`cartilla_acero`, `barras_estandar`), archivo de salida (`resultados_optimizacion`), archivo de configuración del AG.
    *   Opciones para verbosidad.
    *   Comandos para diferentes acciones (ej. `oica run`, `oica tune-params`, `oica visualize`).
    *   Barras de progreso (`tqdm`) para el ciclo del AG.
*   **(Opcional) GUI Simple (con `Streamlit`, `Tkinter`, o `PyQt`/`PySide`):**
    *   Carga de archivos mediante diálogos.
    *   Campos para introducir/modificar parámetros del AG y `LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE`.
    *   Visualización de la tabla de resultados y los patrones de corte.
    *   Un botón "Ejecutar Optimización".
    *   `Streamlit` es particularmente rápido para prototipar UIs de datos.

### **3.2. Visualización de Resultados**

*   **Con `matplotlib` o `plotly`:**
    *   **Visualización de Patrones de Corte:** Para cada patrón en la solución óptima:
        *   Dibujar un rectángulo representando la `origen_barra_longitud`.
        *   Dentro, dibujar segmentos representando las `piezas_cortadas` (quizás con colores diferentes por `id_pedido` o longitud).
        *   Mostrar el `desperdicio_patron_longitud` restante.
    *   **Gráfico de Convergencia del AG:** Mejor fitness vs. generación.
    *   **Estadísticas de Desperdicio:** Gráfico de torta o barras mostrando: longitud total de material original usado, longitud total de piezas útiles cortadas, longitud total de desperdicio (utilizable y no utilizable).
    *   Guardar visualizaciones en archivos de imagen.

### **3.3. Configuración Flexible**

*   **Archivo de Configuración (JSON, YAML, o INI):**
    *   JSON es fácil de parsear en Python. YAML es más legible para humanos.
    *   Parámetros a incluir:
        *   Rutas por defecto a `cartilla_acero.csv` y `barras_estandar.json`.
        *   `LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE`.
        *   Todos los hiperparámetros del AG (los discutidos en 2.1).
        *   Opciones de logging y visualización.
    *   El script debe cargar esta configuración al inicio. Argumentos CLI pueden sobrescribir valores del archivo.

### **3.4. Consideraciones de Restricciones Adicionales (Más allá del MVP)**

*   **Kerf del Corte (Ancho de la Cuchilla/Sierra):**
    *   Si `kerf_width > 0`, cada corte consume material.
    *   Al calcular si una pieza cabe y al calcular el desperdicio, la longitud efectiva de una pieza en una barra es `longitud_pieza_requerida + kerf_width`. El último corte no añade kerf al desperdicio.
    *   Esto debe integrarse en la generación/validación de patrones y en la función de fitness.
*   **Número Máximo de Cortes por Barra:**
    *   Algunas máquinas o procesos pueden tener un límite.
    *   El cromosoma (en cada patrón) necesitaría almacenar el número de cortes.
    *   Añadir una penalización en la función de fitness si se excede este límite.
*   **Optimización Multi-Objetivo (Avanzado):**
    *   Ejemplos de objetivos: [Minimizar desperdicio, Minimizar número de barras estándar usadas, Maximizar uso de desperdicios previos].
    *   **Enfoque Simple:** Combinar objetivos en una función de fitness ponderada: `fitness = w1*obj1 + w2*obj2 + ...`. Los pesos `w1, w2` reflejan la importancia relativa.
    *   **Enfoque Avanzado (NSGA-II, SPEA2):** Algoritmos genéticos multi-objetivo que buscan un conjunto de soluciones en el frente de Pareto (soluciones no dominadas). Esto es significativamente más complejo de implementar.

---

## **Fase 4: Pruebas Exhaustivas y Validación**

Asegurar la robustez y corrección del sistema.

### **4.1. Creación de un Conjunto de Datos de Prueba Extenso y Diverso.**

*   **Escenarios a Cubrir:**
    *   Problemas pequeños (verificables manualmente o con solvers exactos para benchmark).
    *   Problemas medianos y grandes (más realistas).
    *   Variedad en el número de `id_pedido`, `longitud_pieza_requerida`, `cantidad_requerida`.
    *   Diferentes configuraciones de `barras_estandar.json` (pocas/muchas longitudes, longitudes muy diferentes).
    *   Casos con muchos `grupo_ejecucion` para probar el manejo secuencial de desperdicios.
    *   Casos donde las `longitud_pieza_requerida` son muy pequeñas comparadas con las barras estándar (muchos cortes por barra).
    *   Casos donde las `longitud_pieza_requerida` son cercanas a las longitudes de las barras estándar.
    *   Casos con y sin `desperdicios_reutilizables_previos` significativos.

### **4.2. Comparación con Otros Métodos/Software (Benchmarking).**

*   **Heurísticas Simples:** Implementar FFD, BFD, y quizás algunas otras (Worst Fit, etc.) como optimizadores base. Comparar la calidad de sus soluciones (desperdicio) y tiempo de ejecución con el AG.
*   **Solvers Exactos (para problemas pequeños):** Usar una librería de Programación Lineal Entera (PLE) como `PuLP`, `OR-Tools` (de Google), o `SciPy` (con `linprog` para LP, pero CSP es más complejo) para modelar y resolver instancias pequeñas del problema. Esto dará el óptimo real para comparar.
*   **Software Existente:** Si hay software de CSP (incluso académico o de código abierto) disponible, intentar comparar resultados en problemas benchmark comunes si existen.

### **4.3. Validación con Usuarios/Expertos del Dominio.**

*   Presentar los resultados (patrones de corte, cifras de desperdicio) del OICA a ingenieros estructurales, personal de obra, o gerentes de producción de talleres metalmecánicos.
*   Obtener feedback sobre:
    *   La practicidad de los patrones de corte generados.
    *   Si las métricas de desperdicio son las que ellos consideran importantes.
    *   La usabilidad de la interfaz (si se desarrolla una).
    *   Cualquier restricción o consideración del mundo real que no se haya modelado.

---

## **Fase 5: Documentación y Mantenimiento**

Un proyecto bien documentado es más fácil de usar, mantener y extender.

### **5.1. Documentación Completa del Código.**

*   **Docstrings (Google Style o NumPy Style):** Para todos los módulos, clases y funciones. Describir propósito, argumentos (con tipos), qué retorna, y ejemplos de uso si es relevante.
*   **Type Hinting:** Usar type hints de Python en todo el código.
*   **Comentarios en Línea:** Para lógica compleja o decisiones de diseño no obvias.
*   **README.md:** Mantenerlo actualizado con:
    *   Descripción del proyecto y problema.
    *   Instrucciones de instalación y configuración.
    *   Guía de uso rápida (CLI, GUI).
    *   Arquitectura general del software.
    *   Formato de archivos de entrada/salida.

### **5.2. Manual de Usuario Detallado.**

*   Dirigido a usuarios finales no técnicos (o menos técnicos).
*   Explicar cómo preparar los datos de entrada.
*   Cómo ejecutar el optimizador y configurar sus parámetros principales.
*   Cómo interpretar los resultados y visualizaciones.
*   Sección de "Preguntas Frecuentes" (FAQ) o "Solución de Problemas Comunes".

### **5.3. Plan de Mantenimiento y Futuras Actualizaciones.**

*   **Control de Versiones (Git):** Usar `git` desde el inicio. Seguir una estrategia de ramas (ej. `main`, `develop`, `feature/nombre_feature`, `fix/nombre_bug`).
*   **Sistema de Seguimiento de Incidencias (Issue Tracker):** Usar GitHub Issues, GitLab Issues, Jira, etc., para reportar bugs y solicitar nuevas funcionalidades.
*   **Pruebas Automatizadas (con `pytest` o `unittest`):**
    *   **Pruebas Unitarias:** Para funciones individuales (especialmente en el AG: fitness, operadores, utilidades de cromosoma).
    *   **Pruebas de Integración:** Para el flujo completo del script con datos de prueba pequeños.
    *   Buscar una buena cobertura de pruebas.
*   **Integración Continua/Despliegue Continuo (CI/CD) (Opcional, pero buena práctica para proyectos más grandes):**
    *   Usar GitHub Actions, GitLab CI, Jenkins, etc., para ejecutar pruebas automáticamente en cada push o merge request.
*   **Roadmap de Futuras Versiones:** Esbozar posibles mejoras o funcionalidades más allá del alcance actual (ej. integración con bases de datos de inventario, optimización 2D, planificación de múltiples proyectos).

---

Este plan detallado debería proporcionar una base sólida para el desarrollo de OICA. Es importante recordar que es un documento vivo y puede necesitar ajustes a medida que el proyecto avanza y se obtiene más conocimiento. 
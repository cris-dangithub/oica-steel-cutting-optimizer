# Algoritmo Genético para OICA

Este módulo implementa el Algoritmo Genético (AG) para el Optimizador Inteligente de Cortes de Acero (OICA).

## Estructura del Cromosoma

El cromosoma es la estructura de datos fundamental del AG, que representa una posible solución al problema de corte para un subproblema específico (un número de barra y grupo de ejecución).

### Clase `Patron`

Representa un patrón de corte para una barra específica. Define cómo se corta una barra de origen (estándar o desperdicio) en piezas específicas.

#### Atributos principales:

- `origen_barra_longitud`: Longitud de la barra de origen (metros)
- `origen_barra_tipo`: Tipo de barra ('estandar' o 'desperdicio')
- `piezas_cortadas`: Lista de diccionarios con las piezas cortadas
- `desperdicio_patron_longitud`: Valor calculado del desperdicio
- `es_desperdicio_utilizable`: Booleano según el límite mínimo de desperdicio útil

### Clase `Cromosoma`

Representa una solución completa al problema, como una lista de patrones de corte.

#### Atributos principales:

- `patrones`: Lista de objetos `Patron`

## Función de Fitness

La función de fitness evalúa la calidad de un cromosoma, considerando múltiples factores como el desperdicio generado, el cumplimiento de la demanda y otros aspectos. Un valor menor de fitness indica una mejor solución.

### Factores Considerados

1. **Desperdicio Total**: Suma del desperdicio de todos los patrones de corte.
2. **Piezas Faltantes**: Penalización por no cumplir con la demanda requerida.
3. **Piezas Sobrantes**: Penalización por producir más piezas de las necesarias.
4. **Número de Barras Estándar**: Penalización por cada barra estándar utilizada.
5. **Uso de Desperdicios**: Bonificación por utilizar desperdicios previos como origen.

### Configuración de Pesos

La importancia relativa de cada factor se puede ajustar mediante pesos:

```python
config_fitness = {
    'peso_desperdicio': 1.0,                # Factor base para el desperdicio
    'penalizacion_faltantes': 1000.0,       # Penalización por cada unidad de longitud faltante
    'penalizacion_sobrantes': 500.0,        # Penalización por cada unidad de longitud producida en exceso
    'penalizacion_num_barras_estandar': 5.0, # Penalización por cada barra estándar utilizada
    'bonificacion_uso_desperdicios': 3.0    # Bonificación por cada unidad de longitud de desperdicios utilizados
}
```

## Ejemplos de Uso

### Crear un Patrón de Corte

```python
from genetic_algorithm.chromosome import Patron

# Crear un patrón de corte para una barra estándar de 6 metros
patron = Patron(
    origen_barra_longitud=6.0,
    origen_barra_tipo='estandar',
    piezas_cortadas=[
        {'id_pedido': 'P001', 'longitud_pieza': 2.5, 'cantidad_pieza_en_patron': 2},
        {'id_pedido': 'P002', 'longitud_pieza': 1.0, 'cantidad_pieza_en_patron': 1}
    ]
)

# El desperdicio se calcula automáticamente: 6.0 - (2.5*2 + 1.0) = 0.0
print(patron.desperdicio_patron_longitud)  # 0.0
print(patron.es_desperdicio_utilizable)    # False (no hay desperdicio)

# Añadir una pieza al patrón
patron2 = Patron(origen_barra_longitud=3.0, origen_barra_tipo='desperdicio')
patron2.agregar_pieza(id_pedido='P003', longitud_pieza=1.5, cantidad=1)
patron2.agregar_pieza(id_pedido='P004', longitud_pieza=0.75, cantidad=1)
print(patron2.desperdicio_patron_longitud)  # 0.75
print(patron2.es_desperdicio_utilizable)    # True (desperdicio >= 0.5)
```

### Crear un Cromosoma y Analizar su Contenido

```python
from genetic_algorithm.chromosome import Cromosoma, Patron

# Crear patrones de corte
patron1 = Patron(
    origen_barra_longitud=6.0,
    origen_barra_tipo='estandar',
    piezas_cortadas=[
        {'id_pedido': 'P001', 'longitud_pieza': 2.5, 'cantidad_pieza_en_patron': 2},
        {'id_pedido': 'P002', 'longitud_pieza': 1.0, 'cantidad_pieza_en_patron': 1}
    ]
)

patron2 = Patron(
    origen_barra_longitud=3.0,
    origen_barra_tipo='desperdicio',
    piezas_cortadas=[
        {'id_pedido': 'P003', 'longitud_pieza': 1.5, 'cantidad_pieza_en_patron': 1},
        {'id_pedido': 'P004', 'longitud_pieza': 0.75, 'cantidad_pieza_en_patron': 1}
    ]
)

# Crear un cromosoma con ambos patrones
cromosoma = Cromosoma([patron1, patron2])

# Analizar el cromosoma
print(len(cromosoma))                           # 2 (número de patrones)
print(cromosoma.calcular_desperdicio_total())   # 0.75 (suma de desperdicios)
print(cromosoma.obtener_desperdicios_utilizables())  # [0.75]
print(cromosoma.contar_barras_estandar())       # 1
print(cromosoma.contar_desperdicios_usados())   # 1
```

### Validar un Cromosoma contra Requisitos

```python
import pandas as pd
from genetic_algorithm.chromosome_utils import validar_cromosoma_completitud

# Crear un DataFrame de piezas requeridas
piezas_requeridas_df = pd.DataFrame([
    {'id_pedido': 'P001', 'longitud_pieza_requerida': 2.5, 'cantidad_requerida': 2},
    {'id_pedido': 'P002', 'longitud_pieza_requerida': 1.0, 'cantidad_requerida': 1},
    {'id_pedido': 'P003', 'longitud_pieza_requerida': 1.5, 'cantidad_requerida': 1}
])

# El cromosoma del ejemplo anterior tiene:
# - 2 piezas de 2.5m para el pedido P001
# - 1 pieza de 1.0m para el pedido P002
# - 1 pieza de 1.5m para el pedido P003
# - 1 pieza de 0.75m para el pedido P004 (que no está en los requisitos)

# Validar si el cromosoma satisface exactamente la demanda
es_exacto, info = validar_cromosoma_completitud(cromosoma, piezas_requeridas_df)

print(es_exacto)        # False (tiene una pieza de más)
print(info['completo']) # True (cubre todas las piezas requeridas)
print(info['exceso'])   # True (tiene piezas no solicitadas)
print(info['faltantes']) # {} (no hay faltantes)
print(info['sobrantes']) # {('P004', 0.75): 1} (tiene 1 pieza de 0.75m para P004 que no estaba en los requisitos)
```

### Calcular el Fitness de un Cromosoma

```python
import pandas as pd
from genetic_algorithm.chromosome import Patron, Cromosoma
from genetic_algorithm.fitness import calcular_fitness, analizar_componentes_fitness, obtener_config_fitness_default

# Crear un DataFrame de piezas requeridas
piezas_requeridas_df = pd.DataFrame([
    {'id_pedido': 'P001', 'longitud_pieza_requerida': 2.5, 'cantidad_requerida': 2},
    {'id_pedido': 'P002', 'longitud_pieza_requerida': 1.0, 'cantidad_requerida': 3},
    {'id_pedido': 'P003', 'longitud_pieza_requerida': 1.5, 'cantidad_requerida': 1}
])

# Crear un cromosoma para evaluar
patron1 = Patron(
    origen_barra_longitud=6.0,
    origen_barra_tipo='estandar',
    piezas_cortadas=[
        {'id_pedido': 'P001', 'longitud_pieza': 2.5, 'cantidad_pieza_en_patron': 2},
        {'id_pedido': 'P002', 'longitud_pieza': 1.0, 'cantidad_pieza_en_patron': 1}
    ]
)

patron2 = Patron(
    origen_barra_longitud=3.0,
    origen_barra_tipo='desperdicio',
    piezas_cortadas=[
        {'id_pedido': 'P002', 'longitud_pieza': 1.0, 'cantidad_pieza_en_patron': 2},
        {'id_pedido': 'P003', 'longitud_pieza': 1.5, 'cantidad_pieza_en_patron': 1}
    ]
)

cromosoma = Cromosoma([patron1, patron2])

# Obtener configuración de fitness por defecto
config_fitness = obtener_config_fitness_default()

# Calcular fitness del cromosoma
fitness = calcular_fitness(cromosoma, piezas_requeridas_df, config_fitness)
print(f"Fitness del cromosoma: {fitness}")  # Menor valor indica mejor solución

# Analizar componentes del fitness para entender la calidad de la solución
componentes = analizar_componentes_fitness(cromosoma, piezas_requeridas_df, config_fitness)
print(f"Componentes del fitness:")
for componente, valor in componentes.items():
    print(f"  - {componente}: {valor}")
```

### Personalizar la Función de Fitness

```python
# Crear una configuración personalizada que priorice más el uso de desperdicios
config_personalizado = {
    'peso_desperdicio': 2.0,                # Mayor penalización por desperdicio
    'penalizacion_faltantes': 1000.0,       # Misma penalización por piezas faltantes
    'penalizacion_sobrantes': 500.0,        # Misma penalización por piezas sobrantes
    'penalizacion_num_barras_estandar': 10.0, # Mayor penalización por usar barras estándar
    'bonificacion_uso_desperdicios': 5.0    # Mayor bonificación por usar desperdicios
}

# Calcular fitness con la configuración personalizada
fitness_personalizado = calcular_fitness(cromosoma, piezas_requeridas_df, config_personalizado)
```

## Consideraciones para el Algoritmo Genético

1. **Representación**: Cada cromosoma es una lista de patrones que satisface una demanda específica.
2. **Fitness**: Se evalúa principalmente por el desperdicio total, con penalizaciones por piezas faltantes o sobrantes.
3. **Operadores**: Los operadores genéticos (cruce, mutación) manipulan estos patrones para evolucionar soluciones.

Para más detalles sobre la implementación, consultar los archivos:
- `chromosome.py`: Definición de las clases principales
- `chromosome_utils.py`: Funciones utilitarias para manipular cromosomas
- `fitness.py`: Función de fitness y funciones auxiliares para evaluar soluciones 
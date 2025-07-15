#!/usr/bin/env python3
"""
Demostración del Algoritmo Genético para Optimización de Cortes de Acero.

Este script muestra el algoritmo genético funcionando de extremo a extremo
con un ejemplo simple pero realista.
"""

import pandas as pd
from genetic_algorithm.engine import ejecutar_algoritmo_genetico_simple, ejecutar_algoritmo_genetico
from genetic_algorithm.metrics import generar_reporte_evolucion, RegistroEvolucion
from genetic_algorithm.chromosome_utils import calcular_sumario_piezas_en_cromosoma


def demo_basica():
    """Demostración básica del algoritmo genético."""
    print("=" * 60)
    print("DEMOSTRACIÓN BÁSICA DEL ALGORITMO GENÉTICO")
    print("=" * 60)
    print()
    
    # Datos de ejemplo
    piezas_requeridas = pd.DataFrame([
        {'id_pedido': 'P001', 'longitud_pieza_requerida': 2.5, 'cantidad_requerida': 3},
        {'id_pedido': 'P002', 'longitud_pieza_requerida': 1.8, 'cantidad_requerida': 2},
        {'id_pedido': 'P003', 'longitud_pieza_requerida': 3.2, 'cantidad_requerida': 1},
        {'id_pedido': 'P004', 'longitud_pieza_requerida': 1.5, 'cantidad_requerida': 4},
        {'id_pedido': 'P005', 'longitud_pieza_requerida': 2.0, 'cantidad_requerida': 2}
    ])
    
    barras_disponibles = [
        {'longitud': 6.0, 'tipo': 'estandar'},
        {'longitud': 4.0, 'tipo': 'estandar'},
        {'longitud': 8.0, 'tipo': 'estandar'}
    ]
    
    desperdicios_disponibles = [
        {'longitud': 2.8, 'tipo': 'desperdicio'},
        {'longitud': 1.9, 'tipo': 'desperdicio'}
    ]
    
    print("DATOS DEL PROBLEMA:")
    print(f"Piezas requeridas: {len(piezas_requeridas)} tipos")
    print(f"Barras disponibles: {len(barras_disponibles)} tipos")
    print(f"Desperdicios disponibles: {len(desperdicios_disponibles)} piezas")
    print()
    
    print("PIEZAS REQUERIDAS:")
    for _, pieza in piezas_requeridas.iterrows():
        print(f"  {pieza['id_pedido']}: {pieza['cantidad_requerida']}x {pieza['longitud_pieza_requerida']}m")
    print()
    
    print("EJECUTANDO ALGORITMO GENÉTICO...")
    print()
    
    # Ejecutar algoritmo genético
    mejor_cromosoma = ejecutar_algoritmo_genetico_simple(
        piezas_requeridas,
        barras_disponibles,
        desperdicios_disponibles,
        max_generaciones=20,
        tamaño_poblacion=15
    )
    
    print()
    print("RESULTADO OBTENIDO:")
    print(f"Número de patrones de corte: {len(mejor_cromosoma.patrones)}")
    print(f"Desperdicio total: {mejor_cromosoma.calcular_desperdicio_total():.2f}m")
    print(f"Barras estándar utilizadas: {mejor_cromosoma.contar_barras_estandar()}")
    
    # Contar desperdicios reutilizados manualmente
    desperdicios_reutilizados = sum(1 for p in mejor_cromosoma.patrones if p.origen_barra_tipo == 'desperdicio')
    print(f"Desperdicios reutilizados: {desperdicios_reutilizados}")
    print()
    
    print("PATRONES DE CORTE GENERADOS:")
    for i, patron in enumerate(mejor_cromosoma.patrones, 1):
        print(f"  Patrón {i}: Barra {patron.origen_barra_tipo} de {patron.origen_barra_longitud}m")
        for pieza in patron.piezas_cortadas:
            print(f"    → {pieza['cantidad_pieza_en_patron']}x {pieza['longitud_pieza']}m ({pieza['id_pedido']})")
        print(f"    Desperdicio: {patron.desperdicio_patron_longitud:.2f}m")
        print()


def demo_avanzada():
    """Demostración avanzada con configuración personalizada y métricas detalladas."""
    print("=" * 60)
    print("DEMOSTRACIÓN AVANZADA CON MÉTRICAS DETALLADAS")
    print("=" * 60)
    print()
    
    # Problema más complejo
    piezas_requeridas = pd.DataFrame([
        {'id_pedido': 'A001', 'longitud_pieza_requerida': 2.3, 'cantidad_requerida': 5},
        {'id_pedido': 'A002', 'longitud_pieza_requerida': 1.7, 'cantidad_requerida': 3},
        {'id_pedido': 'A003', 'longitud_pieza_requerida': 3.1, 'cantidad_requerida': 2},
        {'id_pedido': 'A004', 'longitud_pieza_requerida': 1.2, 'cantidad_requerida': 6},
        {'id_pedido': 'A005', 'longitud_pieza_requerida': 2.8, 'cantidad_requerida': 3},
        {'id_pedido': 'A006', 'longitud_pieza_requerida': 1.9, 'cantidad_requerida': 4}
    ])
    
    barras_disponibles = [
        {'longitud': 6.0, 'tipo': 'estandar'},
        {'longitud': 4.5, 'tipo': 'estandar'},
        {'longitud': 8.0, 'tipo': 'estandar'}
    ]
    
    desperdicios_disponibles = [
        {'longitud': 3.2, 'tipo': 'desperdicio'},
        {'longitud': 2.1, 'tipo': 'desperdicio'},
        {'longitud': 1.8, 'tipo': 'desperdicio'}
    ]
    
    # Configuración personalizada
    config_personalizada = {
        'tamaño_poblacion': 25,
        'max_generaciones': 30,
        'estrategia_inicializacion': 'hibrida',
        'metodo_seleccion': 'torneo',
        'tamaño_torneo': 4,
        'tasa_cruce': 0.85,
        'estrategia_cruce': 'basado_en_piezas',
        'tasa_mutacion_individuo': 0.25,
        'tasa_mutacion_gen': 0.15,
        'elitismo': True,
        'tamaño_elite': 3,
        'criterio_convergencia': 'generaciones_sin_mejora',
        'generaciones_sin_mejora_max': 10,
        'tiempo_limite_segundos': 60,
        'logging_habilitado': True,
        'logging_frecuencia': 5
    }
    
    print("CONFIGURACIÓN PERSONALIZADA:")
    for clave, valor in config_personalizada.items():
        print(f"  {clave}: {valor}")
    print()
    
    print("EJECUTANDO ALGORITMO GENÉTICO AVANZADO...")
    print()
    
    # Ejecutar con configuración personalizada
    mejor_cromosoma, estadisticas = ejecutar_algoritmo_genetico(
        piezas_requeridas,
        barras_disponibles,
        desperdicios_disponibles,
        config_personalizada
    )
    
    print()
    print("ESTADÍSTICAS DE EVOLUCIÓN:")
    print(f"  Mejor fitness encontrado: {estadisticas['mejor_fitness_global']:.4f}")
    print(f"  Generación del mejor: {estadisticas['generacion_mejor_global']}")
    print(f"  Generaciones ejecutadas: {estadisticas['generaciones_ejecutadas']}")
    print(f"  Tiempo total: {estadisticas['tiempo_total_segundos']:.2f} segundos")
    print(f"  Evaluaciones de fitness: {estadisticas['evaluaciones_fitness_total']}")
    print(f"  Convergencia detectada: {'Sí' if estadisticas['convergencia_detectada'] else 'No'}")
    print()
    
    print("ANÁLISIS DE LA SOLUCIÓN:")
    sumario_piezas = calcular_sumario_piezas_en_cromosoma(mejor_cromosoma)
    print(f"  Patrones de corte: {len(mejor_cromosoma.patrones)}")
    print(f"  Desperdicio total: {mejor_cromosoma.calcular_desperdicio_total():.2f}m")
    print(f"  Eficiencia material: {(1 - mejor_cromosoma.calcular_desperdicio_total() / sum(p.origen_barra_longitud for p in mejor_cromosoma.patrones)) * 100:.1f}%")
    print(f"  Piezas diferentes cortadas: {len(sumario_piezas)}")
    print()
    
    # Verificar completitud
    print("VERIFICACIÓN DE DEMANDA:")
    for _, pieza_req in piezas_requeridas.iterrows():
        id_pedido = pieza_req['id_pedido']
        longitud_req = pieza_req['longitud_pieza_requerida']
        cantidad_req = pieza_req['cantidad_requerida']
        
        # Buscar en el sumario usando la clave (id_pedido, longitud)
        cantidad_cortada = sumario_piezas.get((id_pedido, longitud_req), 0)
        estado = "✅" if cantidad_cortada >= cantidad_req else "❌"
        print(f"  {id_pedido}: {cantidad_cortada}/{cantidad_req} {estado}")


def main():
    """Función principal que ejecuta las demostraciones."""
    print("OICA - Optimizador Inteligente de Cortes de Acero")
    print("Demostración del Algoritmo Genético")
    print()
    
    try:
        # Demostración básica
        demo_basica()
        
        print("\n" + "="*60 + "\n")
        
        # Demostración avanzada
        demo_avanzada()
        
        print("\n" + "="*60)
        print("DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
        print("El algoritmo genético está funcionando correctamente.")
        print("="*60)
        
    except Exception as e:
        print(f"Error durante la demostración: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 
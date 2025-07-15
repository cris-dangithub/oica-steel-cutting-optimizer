#!/usr/bin/env python3
"""
Script de demostración de la integración completa del sistema OICA.

Este script demuestra que el algoritmo genético está correctamente integrado
en el flujo principal del sistema.
"""

import pandas as pd
import time
from main import algoritmo_optimizacion_corte, consolidar_desperdicios, generar_metricas_desperdicios

def demo_integracion_basica():
    """Demostración básica de la integración."""
    print("=== DEMO: Integración Básica del Sistema OICA ===\n")
    
    # Datos de prueba
    piezas_df = pd.DataFrame([
        {'id_pedido': 'P001', 'longitud_pieza_requerida': 2.5, 'cantidad_requerida': 2},
        {'id_pedido': 'P002', 'longitud_pieza_requerida': 1.8, 'cantidad_requerida': 3},
        {'id_pedido': 'P003', 'longitud_pieza_requerida': 3.2, 'cantidad_requerida': 1},
        {'id_pedido': 'P004', 'longitud_pieza_requerida': 1.5, 'cantidad_requerida': 2}
    ])
    
    barras_disponibles = [6.0, 4.0, 8.0]
    desperdicios_previos = [2.8, 1.9]
    
    print("Datos de entrada:")
    print(f"- Piezas requeridas: {len(piezas_df)} tipos")
    print(f"- Barras disponibles: {barras_disponibles}")
    print(f"- Desperdicios previos: {desperdicios_previos}")
    
    # Configuración rápida para demo
    config = {
        'perfil': 'rapido',
        'parametros': {
            'tamaño_poblacion': 10,
            'max_generaciones': 8,
            'logging_habilitado': True
        }
    }
    
    print(f"\nConfiguración del AG: {config['perfil']}")
    print("Ejecutando algoritmo de optimización...")
    
    inicio = time.time()
    
    try:
        patrones, desperdicios = algoritmo_optimizacion_corte(
            piezas_df,
            barras_disponibles,
            desperdicios_previos,
            config
        )
        
        tiempo_total = time.time() - inicio
        
        print(f"\n✅ Optimización completada en {tiempo_total:.2f} segundos")
        print(f"📊 Resultados:")
        print(f"   - Patrones generados: {len(patrones)}")
        print(f"   - Desperdicios nuevos: {len(desperdicios)}")
        
        # Mostrar algunos patrones
        print(f"\n📋 Primeros patrones generados:")
        for i, patron in enumerate(patrones[:3]):
            print(f"   Patrón {i+1}:")
            print(f"     - Barra origen: {patron['barra_origen_longitud']}m")
            print(f"     - Cortes: {patron['cortes_realizados']}")
            print(f"     - Desperdicio: {patron['desperdicio_resultante']}m")
        
        if desperdicios:
            print(f"\n♻️  Desperdicios utilizables: {desperdicios}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la optimización: {e}")
        return False

def demo_gestion_desperdicios():
    """Demostración de la gestión avanzada de desperdicios."""
    print("\n=== DEMO: Gestión Avanzada de Desperdicios ===\n")
    
    desperdicios_test = [2.5, 2.51, 1.8, 0.3, 2.49, 3.0, 1.79, 0.4, 2.52]
    print(f"Desperdicios originales: {desperdicios_test}")
    
    # Consolidar desperdicios
    consolidados = consolidar_desperdicios(desperdicios_test, 0.5, 0.05)
    print(f"Desperdicios consolidados: {consolidados}")
    
    # Generar métricas
    desperdicios_por_tipo = {
        '#4': [2.5, 1.8, 3.0],
        '#5': [1.2, 2.2],
        '#6': []
    }
    
    resultados_df = pd.DataFrame([
        {'barra_origen_longitud': 6.0, 'desperdicio_resultante': 0.5},
        {'barra_origen_longitud': 4.0, 'desperdicio_resultante': 0.8},
        {'barra_origen_longitud': 8.0, 'desperdicio_resultante': 1.2}
    ])
    
    metricas = generar_metricas_desperdicios(desperdicios_por_tipo, resultados_df)
    
    print(f"\n📈 Métricas de desperdicios:")
    print(f"   - Eficiencia global: {metricas['eficiencia_global']:.2f}%")
    print(f"   - Desperdicios finales: {metricas['desperdicios_finales_total']} piezas")
    print(f"   - Longitud total desperdicios: {metricas['desperdicios_finales_longitud']:.2f}m")

def demo_diferentes_configuraciones():
    """Demostración con diferentes configuraciones del AG."""
    print("\n=== DEMO: Diferentes Configuraciones del AG ===\n")
    
    # Datos de prueba más complejos
    piezas_df = pd.DataFrame([
        {'id_pedido': f'P{i:03d}', 'longitud_pieza_requerida': 1.0 + (i % 4) * 0.5, 'cantidad_requerida': 1 + (i % 2)}
        for i in range(10)
    ])
    
    barras_disponibles = [6.0, 8.0, 12.0]
    desperdicios_previos = [2.5, 1.8, 3.2]
    
    configuraciones = [
        ('Rápido', {'perfil': 'rapido', 'parametros': {'logging_habilitado': False}}),
        ('Balanceado', {'perfil': 'balanceado', 'parametros': {'logging_habilitado': False}})
    ]
    
    resultados = {}
    
    for nombre, config in configuraciones:
        print(f"Probando configuración: {nombre}")
        inicio = time.time()
        
        try:
            patrones, desperdicios = algoritmo_optimizacion_corte(
                piezas_df,
                barras_disponibles,
                desperdicios_previos,
                config
            )
            
            tiempo = time.time() - inicio
            resultados[nombre] = {
                'patrones': len(patrones),
                'desperdicios': len(desperdicios),
                'tiempo': tiempo,
                'exito': True
            }
            
            print(f"   ✅ {len(patrones)} patrones en {tiempo:.2f}s")
            
        except Exception as e:
            resultados[nombre] = {'exito': False, 'error': str(e)}
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Resumen de configuraciones:")
    for nombre, resultado in resultados.items():
        if resultado['exito']:
            print(f"   {nombre}: {resultado['patrones']} patrones, {resultado['tiempo']:.2f}s")
        else:
            print(f"   {nombre}: Error - {resultado['error']}")

def main():
    """Función principal del demo."""
    print("🚀 DEMOSTRACIÓN DE INTEGRACIÓN COMPLETA - SISTEMA OICA")
    print("=" * 60)
    
    # Demo 1: Integración básica
    exito_basico = demo_integracion_basica()
    
    # Demo 2: Gestión de desperdicios
    demo_gestion_desperdicios()
    
    # Demo 3: Diferentes configuraciones
    demo_diferentes_configuraciones()
    
    print("\n" + "=" * 60)
    if exito_basico:
        print("✅ INTEGRACIÓN COMPLETADA EXITOSAMENTE")
        print("🎯 El algoritmo genético está correctamente integrado en el flujo principal")
        print("📈 Todas las funcionalidades están operativas")
    else:
        print("❌ PROBLEMAS DETECTADOS EN LA INTEGRACIÓN")
        print("🔧 Revisar logs para más detalles")
    
    print("\n🏁 Demo completado.")

if __name__ == "__main__":
    main() 
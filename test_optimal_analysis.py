#!/usr/bin/env python3
"""
Script de prueba para el análisis de optimización óptima.
"""

import pandas as pd
from genetic_algorithm.optimal_analyzer import (
    calcular_solucion_optima_homogenea,
    analizar_casos_homogeneos,
    generar_reporte_optimizacion
)

def main():
    print("🔍 PRUEBA DE ANÁLISIS ÓPTIMO - CASO BARRAS #3")
    print("=" * 50)
    
    # Caso específico: Barras #3
    longitud_pieza = 1.08
    cantidad_requerida = 459
    longitudes_barras = [6.0, 9.0, 12.0]
    
    print(f"📊 DATOS DEL PROBLEMA:")
    print(f"- Longitud de pieza: {longitud_pieza}m")
    print(f"- Cantidad requerida: {cantidad_requerida} piezas")
    print(f"- Longitudes de barras disponibles: {longitudes_barras}")
    print()
    
    # Calcular solución óptima
    solucion_optima = calcular_solucion_optima_homogenea(
        longitud_pieza, cantidad_requerida, longitudes_barras
    )
    
    print("✅ SOLUCIÓN ÓPTIMA CALCULADA:")
    print(f"- Combinación de barras: {solucion_optima['combinacion_barras']}")
    print(f"- Total de barras: {solucion_optima['num_barras_total']}")
    print(f"- Piezas producidas: {solucion_optima['piezas_producidas']}")
    print(f"- Piezas en exceso: {solucion_optima['piezas_exceso']}")
    print(f"- Desperdicio total: {solucion_optima['desperdicio_total']:.2f}m")
    print(f"- Eficiencia: {solucion_optima['eficiencia']*100:.2f}%")
    print()
    
    # Verificar cálculo manual del usuario
    print("🧮 VERIFICACIÓN DEL CÁLCULO MANUAL:")
    
    # Cálculo del usuario: 41 barras de 12m + 1 barra de 9m
    barras_12m = 41
    barras_9m = 1
    
    piezas_con_12m = barras_12m * (12.0 // longitud_pieza)  # 41 * 11
    piezas_con_9m = barras_9m * (9.0 // longitud_pieza)    # 1 * 8
    
    piezas_totales_manual = piezas_con_12m + piezas_con_9m
    
    desperdicio_12m = barras_12m * (12.0 % longitud_pieza)  # 41 * 0.12
    desperdicio_9m = barras_9m * (9.0 % longitud_pieza)     # 1 * 0.36
    
    desperdicio_total_manual = desperdicio_12m + desperdicio_9m
    
    material_total_manual = barras_12m * 12.0 + barras_9m * 9.0
    eficiencia_manual = 1 - (desperdicio_total_manual / material_total_manual)
    
    print(f"- Solución manual: {barras_12m} barras de 12m + {barras_9m} barra de 9m")
    print(f"- Piezas producidas: {int(piezas_totales_manual)} ({int(piezas_totales_manual - cantidad_requerida)} exceso)")
    print(f"- Desperdicio total: {desperdicio_total_manual:.2f}m")
    print(f"- Eficiencia: {eficiencia_manual*100:.2f}%")
    print()
    
    # Comparar
    print("⚖️ COMPARACIÓN:")
    coinciden = (
        solucion_optima['combinacion_barras'][12.0] == barras_12m and
        solucion_optima['combinacion_barras'][9.0] == barras_9m and
        solucion_optima['combinacion_barras'][6.0] == 0
    )
    
    if coinciden:
        print("✅ ¡El análisis óptimo COINCIDE con el cálculo manual!")
    else:
        print("❌ El análisis óptimo DIFIERE del cálculo manual")
        print(f"   Algoritmo sugiere: {solucion_optima['combinacion_barras']}")
        print(f"   Cálculo manual: 12m:{barras_12m}, 9m:{barras_9m}, 6m:0")
    
    print()
    
    # Comparar con resultado de la IA
    print("🤖 COMPARACIÓN CON RESULTADO DE LA IA:")
    barras_ia = 92  # Según el resultado anterior
    desperdicio_ia = 92 * (6.0 % longitud_pieza)  # 92 * 0.6
    eficiencia_ia = 0.898  # 89.8% según reporte
    
    print(f"- Solución IA: {barras_ia} barras de 6m")
    print(f"- Desperdicio IA: {desperdicio_ia:.2f}m")
    print(f"- Eficiencia IA: {eficiencia_ia*100:.1f}%")
    print()
    
    print("📈 MEJORAS CONSEGUIDAS:")
    mejora_barras = barras_ia - solucion_optima['num_barras_total']
    mejora_desperdicio = desperdicio_ia - solucion_optima['desperdicio_total']
    mejora_eficiencia = solucion_optima['eficiencia'] - eficiencia_ia
    
    print(f"- Ahorro en barras: {mejora_barras} barras ({mejora_barras/barras_ia*100:.1f}%)")
    print(f"- Reducción de desperdicio: {mejora_desperdicio:.2f}m ({mejora_desperdicio/desperdicio_ia*100:.1f}%)")
    print(f"- Mejora en eficiencia: {mejora_eficiencia*100:.2f} puntos porcentuales")
    
    print()
    print("🎯 CONCLUSIÓN:")
    print("El algoritmo genético actual tiene una falla crítica en la evaluación")
    print("de combinaciones óptimas de longitudes de barras para casos homogéneos.")


if __name__ == "__main__":
    main() 
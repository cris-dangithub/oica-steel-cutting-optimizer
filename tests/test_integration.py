"""
Tests de integración para el sistema OICA completo.

Estos tests validan que el algoritmo genético funciona correctamente
integrado en el flujo principal del sistema.
"""

import unittest
import pandas as pd
import tempfile
import json
import os
from unittest.mock import patch

# Importar módulos del sistema
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    algoritmo_optimizacion_corte,
    consolidar_desperdicios,
    priorizar_desperdicios,
    generar_metricas_desperdicios,
    cargar_cartilla_acero,
    cargar_barras_estandar,
    _algoritmo_respaldo_ffd
)
from genetic_algorithm.output_formatter import formatear_salida_desde_cromosoma
from genetic_algorithm.input_adapter import adaptar_entrada_completa


class TestIntegracionCompleta(unittest.TestCase):
    """Tests de integración del sistema completo."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Datos de prueba para piezas requeridas
        self.piezas_requeridas_df = pd.DataFrame([
            {'id_pedido': 'P001', 'longitud_pieza_requerida': 2.5, 'cantidad_requerida': 3},
            {'id_pedido': 'P002', 'longitud_pieza_requerida': 1.8, 'cantidad_requerida': 2},
            {'id_pedido': 'P003', 'longitud_pieza_requerida': 3.2, 'cantidad_requerida': 1},
            {'id_pedido': 'P004', 'longitud_pieza_requerida': 1.5, 'cantidad_requerida': 4}
        ])
        
        # Barras estándar disponibles
        self.barras_disponibles = [6.0, 4.0, 8.0]
        
        # Desperdicios previos
        self.desperdicios_previos = [2.8, 1.9, 3.1]
        
        # Configuración rápida para tests
        self.config_test = {
            'perfil': 'rapido',
            'parametros': {
                'tamaño_poblacion': 8,
                'max_generaciones': 5,
                'logging_habilitado': False
            }
        }
    
    def test_algoritmo_optimizacion_completo(self):
        """Test del algoritmo de optimización completo."""
        patrones, desperdicios = algoritmo_optimizacion_corte(
            self.piezas_requeridas_df,
            self.barras_disponibles,
            self.desperdicios_previos,
            self.config_test
        )
        
        # Verificar que se generaron patrones
        self.assertIsInstance(patrones, list)
        self.assertGreater(len(patrones), 0)
        
        # Verificar estructura de patrones
        for patron in patrones:
            self.assertIsInstance(patron, dict)
            self.assertIn('barra_origen_longitud', patron)
            self.assertIn('cortes_realizados', patron)
            self.assertIn('piezas_obtenidas', patron)
            self.assertIn('desperdicio_resultante', patron)
            
            # Verificar consistencia matemática
            suma_cortes = sum(patron['cortes_realizados'])
            total_esperado = suma_cortes + patron['desperdicio_resultante']
            self.assertAlmostEqual(total_esperado, patron['barra_origen_longitud'], places=2)
        
        # Verificar desperdicios
        self.assertIsInstance(desperdicios, list)
        for desperdicio in desperdicios:
            self.assertIsInstance(desperdicio, (int, float))
            self.assertGreaterEqual(desperdicio, 0.5)  # Longitud mínima
    
    def test_diferentes_perfiles_configuracion(self):
        """Test con diferentes perfiles de configuración."""
        perfiles = ['rapido', 'balanceado']
        
        for perfil in perfiles:
            with self.subTest(perfil=perfil):
                config = {'perfil': perfil, 'parametros': {'logging_habilitado': False}}
                
                patrones, desperdicios = algoritmo_optimizacion_corte(
                    self.piezas_requeridas_df,
                    self.barras_disponibles,
                    self.desperdicios_previos,
                    config
                )
                
                self.assertIsInstance(patrones, list)
                self.assertIsInstance(desperdicios, list)
    
    def test_algoritmo_respaldo_ffd(self):
        """Test del algoritmo de respaldo First Fit Decreasing."""
        patrones, desperdicios = _algoritmo_respaldo_ffd(
            self.piezas_requeridas_df,
            self.barras_disponibles,
            self.desperdicios_previos
        )
        
        # Verificar que se generaron patrones
        self.assertIsInstance(patrones, list)
        self.assertGreater(len(patrones), 0)
        
        # Verificar estructura
        for patron in patrones:
            self.assertIn('barra_origen_longitud', patron)
            self.assertIn('cortes_realizados', patron)
            self.assertIn('piezas_obtenidas', patron)
            self.assertIn('desperdicio_resultante', patron)
    
    def test_manejo_errores_algoritmo(self):
        """Test del manejo de errores en el algoritmo."""
        # DataFrame vacío
        df_vacio = pd.DataFrame(columns=['id_pedido', 'longitud_pieza_requerida', 'cantidad_requerida'])
        
        # Debería manejar el error graciosamente
        try:
            patrones, desperdicios = algoritmo_optimizacion_corte(
                df_vacio,
                self.barras_disponibles,
                self.desperdicios_previos,
                self.config_test
            )
            # Si no falla, debería retornar listas vacías o usar el algoritmo de respaldo
            self.assertIsInstance(patrones, list)
            self.assertIsInstance(desperdicios, list)
        except Exception as e:
            self.fail(f"El algoritmo no manejó correctamente el DataFrame vacío: {e}")
    
    def test_consolidacion_desperdicios(self):
        """Test de la función de consolidación de desperdicios."""
        desperdicios_test = [2.5, 2.51, 1.8, 0.3, 2.49, 3.0, 1.79]
        
        consolidados = consolidar_desperdicios(desperdicios_test, 0.5, 0.05)
        
        # Verificar que se eliminaron los muy pequeños
        self.assertNotIn(0.3, consolidados)
        
        # Verificar que se consolidaron los similares
        similares_25 = [d for d in consolidados if 2.4 <= d <= 2.6]
        self.assertEqual(len(similares_25), 1)  # Solo debería quedar uno
        
        # Verificar orden descendente
        self.assertEqual(consolidados, sorted(consolidados, reverse=True))
    
    def test_priorizacion_desperdicios(self):
        """Test de la función de priorización de desperdicios."""
        desperdicios_test = [1.5, 3.0, 2.2, 1.8, 2.8]
        
        # Test mayor primero
        mayor_primero = priorizar_desperdicios(desperdicios_test, 'mayor_primero')
        self.assertEqual(mayor_primero, sorted(desperdicios_test, reverse=True))
        
        # Test menor primero
        menor_primero = priorizar_desperdicios(desperdicios_test, 'menor_primero')
        self.assertEqual(menor_primero, sorted(desperdicios_test))
        
        # Test balanceado
        balanceado = priorizar_desperdicios(desperdicios_test, 'balanceado')
        self.assertIsInstance(balanceado, list)
        self.assertEqual(len(balanceado), len(desperdicios_test))
    
    def test_metricas_desperdicios(self):
        """Test de generación de métricas de desperdicios."""
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
        
        # Verificar estructura de métricas
        self.assertIn('desperdicios_finales_total', metricas)
        self.assertIn('desperdicios_finales_longitud', metricas)
        self.assertIn('desperdicios_por_tipo', metricas)
        self.assertIn('eficiencia_global', metricas)
        
        # Verificar cálculos
        self.assertEqual(metricas['desperdicios_finales_total'], 5)  # 3 + 2 + 0
        self.assertAlmostEqual(metricas['desperdicios_finales_longitud'], 10.7, places=1)  # 7.3 + 3.4 + 0
        
        # Verificar eficiencia
        self.assertGreater(metricas['eficiencia_global'], 0)
        self.assertLessEqual(metricas['eficiencia_global'], 100)


class TestCargaDatos(unittest.TestCase):
    """Tests para las funciones de carga de datos."""
    
    def test_cargar_cartilla_acero_valida(self):
        """Test de carga de cartilla de acero válida."""
        # Crear archivo temporal con datos válidos
        datos_cartilla = {
            'id_pedido': ['P001', 'P002', 'P003'],
            'numero_barra': ['#4', '#4', '#5'],
            'longitud_pieza_requerida': [2.5, 1.8, 3.2],
            'cantidad_requerida': [3, 2, 1],
            'grupo_ejecucion': [1, 1, 2]
        }
        df_test = pd.DataFrame(datos_cartilla)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df_test.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            df_cargado = cargar_cartilla_acero(temp_file)
            
            self.assertFalse(df_cargado.empty)
            self.assertEqual(len(df_cargado), 3)
            
            # Verificar columnas
            columnas_esperadas = ['id_pedido', 'numero_barra', 'longitud_pieza_requerida', 'cantidad_requerida', 'grupo_ejecucion']
            for col in columnas_esperadas:
                self.assertIn(col, df_cargado.columns)
        
        finally:
            os.unlink(temp_file)
    
    def test_cargar_barras_estandar_validas(self):
        """Test de carga de barras estándar válidas."""
        datos_barras = {
            "#4": [6.0, 12.0],
            "#5": [6.0, 9.0, 12.0],
            "#6": [6.0, 12.0]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(datos_barras, f)
            temp_file = f.name
        
        try:
            barras_cargadas = cargar_barras_estandar(temp_file)
            
            self.assertIsInstance(barras_cargadas, dict)
            self.assertEqual(len(barras_cargadas), 3)
            self.assertIn('#4', barras_cargadas)
            self.assertEqual(barras_cargadas['#4'], [6.0, 12.0])
        
        finally:
            os.unlink(temp_file)
    
    def test_cargar_archivo_inexistente(self):
        """Test de manejo de archivos inexistentes."""
        df_vacio = cargar_cartilla_acero('archivo_inexistente.csv')
        self.assertTrue(df_vacio.empty)
        
        dict_vacio = cargar_barras_estandar('archivo_inexistente.json')
        self.assertEqual(dict_vacio, {})


class TestAdaptadoresFormateadores(unittest.TestCase):
    """Tests para adaptadores de entrada y formateadores de salida."""
    
    def setUp(self):
        """Configuración inicial."""
        self.piezas_df = pd.DataFrame([
            {'id_pedido': 'P001', 'longitud_pieza_requerida': 2.5, 'cantidad_requerida': 2},
            {'id_pedido': 'P002', 'longitud_pieza_requerida': 1.8, 'cantidad_requerida': 1}
        ])
        self.barras_disponibles = [6.0, 4.0]
        self.desperdicios_previos = [2.8, 1.9]
    
    def test_adaptador_entrada_completo(self):
        """Test del adaptador de entrada completo."""
        piezas_adaptadas, barras_dict, desperdicios_dict, resumen = adaptar_entrada_completa(
            self.piezas_df,
            self.barras_disponibles,
            self.desperdicios_previos,
            longitud_minima_desperdicio=0.5,
            consolidar_piezas=True,
            limpiar_datos=True
        )
        
        # Verificar piezas adaptadas
        self.assertIsInstance(piezas_adaptadas, pd.DataFrame)
        self.assertFalse(piezas_adaptadas.empty)
        
        # Verificar barras
        self.assertIsInstance(barras_dict, list)
        self.assertGreater(len(barras_dict), 0)
        for barra in barras_dict:
            self.assertIn('longitud', barra)
            self.assertIn('tipo', barra)
            self.assertEqual(barra['tipo'], 'estandar')
        
        # Verificar desperdicios
        self.assertIsInstance(desperdicios_dict, list)
        for desperdicio in desperdicios_dict:
            self.assertIn('longitud', desperdicio)
            self.assertIn('tipo', desperdicio)
            self.assertEqual(desperdicio['tipo'], 'desperdicio')
        
        # Verificar resumen
        self.assertIsInstance(resumen, dict)
        self.assertIn('piezas', resumen)
        self.assertIn('barras_estandar', resumen)
        self.assertIn('desperdicios_previos', resumen)


class TestRendimientoIntegracion(unittest.TestCase):
    """Tests de rendimiento y escalabilidad."""
    
    def test_problema_mediano(self):
        """Test con un problema de tamaño mediano."""
        # Generar problema más grande
        piezas_grandes = []
        for i in range(20):
            piezas_grandes.append({
                'id_pedido': f'P{i:03d}',
                'longitud_pieza_requerida': 1.0 + (i % 5) * 0.5,
                'cantidad_requerida': 1 + (i % 3)
            })
        
        df_grande = pd.DataFrame(piezas_grandes)
        barras_disponibles = [6.0, 4.0, 8.0, 12.0]
        desperdicios_previos = [2.5, 1.8, 3.2, 1.5]
        
        config_rapida = {
            'perfil': 'rapido',
            'parametros': {
                'tamaño_poblacion': 10,
                'max_generaciones': 8,
                'logging_habilitado': False,
                'tiempo_limite_segundos': 30
            }
        }
        
        import time
        inicio = time.time()
        
        patrones, desperdicios = algoritmo_optimizacion_corte(
            df_grande,
            barras_disponibles,
            desperdicios_previos,
            config_rapida
        )
        
        tiempo_total = time.time() - inicio
        
        # Verificar que se completó en tiempo razonable
        self.assertLess(tiempo_total, 60)  # Menos de 1 minuto
        
        # Verificar que se generaron resultados
        self.assertIsInstance(patrones, list)
        self.assertGreater(len(patrones), 0)
    
    def test_casos_limite(self):
        """Test con casos límite."""
        # Caso 1: Una sola pieza muy grande
        df_pieza_grande = pd.DataFrame([
            {'id_pedido': 'P001', 'longitud_pieza_requerida': 15.0, 'cantidad_requerida': 1}
        ])
        
        patrones, desperdicios = algoritmo_optimizacion_corte(
            df_pieza_grande,
            [6.0, 12.0],
            [],
            {'perfil': 'rapido', 'parametros': {'logging_habilitado': False}}
        )
        
        # Debería usar el algoritmo de respaldo o manejar el caso
        self.assertIsInstance(patrones, list)
        self.assertIsInstance(desperdicios, list)
        
        # Caso 2: Muchas piezas muy pequeñas
        df_piezas_pequenas = pd.DataFrame([
            {'id_pedido': f'P{i:03d}', 'longitud_pieza_requerida': 0.2, 'cantidad_requerida': 1}
            for i in range(50)
        ])
        
        patrones, desperdicios = algoritmo_optimizacion_corte(
            df_piezas_pequenas,
            [6.0],
            [],
            {'perfil': 'rapido', 'parametros': {'logging_habilitado': False}}
        )
        
        self.assertIsInstance(patrones, list)
        self.assertIsInstance(desperdicios, list)


if __name__ == '__main__':
    # Configurar el path para importar módulos
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    unittest.main(verbosity=2) 
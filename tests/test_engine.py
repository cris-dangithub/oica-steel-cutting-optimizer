"""
Tests unitarios para el motor del algoritmo genético.
"""

import unittest
import pandas as pd
import time

from genetic_algorithm.engine import (
    ejecutar_algoritmo_genetico,
    ejecutar_algoritmo_genetico_simple,
    verificar_criterios_parada,
    aplicar_elitismo_y_reemplazo,
    validar_configuracion_ga
)
from genetic_algorithm.chromosome import Patron, Cromosoma
from genetic_algorithm.metrics import RegistroEvolucion
from genetic_algorithm import CONFIG_GA_DEFAULT


class TestEngine(unittest.TestCase):
    """Tests para el motor del algoritmo genético."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.piezas_requeridas_df = pd.DataFrame([
            {'id_pedido': 'P001', 'longitud_pieza_requerida': 2.0, 'cantidad_requerida': 2},
            {'id_pedido': 'P002', 'longitud_pieza_requerida': 1.5, 'cantidad_requerida': 2},
            {'id_pedido': 'P003', 'longitud_pieza_requerida': 1.0, 'cantidad_requerida': 1}
        ])
        
        self.barras_disponibles = [
            {'longitud': 6.0, 'tipo': 'estandar'},
            {'longitud': 4.0, 'tipo': 'estandar'}
        ]
        
        self.desperdicios_disponibles = [
            {'longitud': 2.5, 'tipo': 'desperdicio'}
        ]
        
        # Configuración mínima para tests rápidos
        self.config_test = {
            'tamaño_poblacion': 6,
            'max_generaciones': 5,
            'estrategia_inicializacion': 'heuristica',
            'metodo_seleccion': 'torneo',
            'tamaño_torneo': 2,
            'tasa_cruce': 0.8,
            'estrategia_cruce': 'un_punto',
            'tasa_mutacion_individuo': 0.3,
            'tasa_mutacion_gen': 0.1,
            'elitismo': True,
            'tamaño_elite': 1,
            'criterio_convergencia': 'generaciones_sin_mejora',
            'generaciones_sin_mejora_max': 3,
            'tiempo_limite_segundos': 30,
            'logging_habilitado': False
        }
    
    def test_ejecutar_algoritmo_genetico_basico(self):
        """Test básico de ejecución del algoritmo genético."""
        mejor_cromosoma, estadisticas = ejecutar_algoritmo_genetico(
            self.piezas_requeridas_df,
            self.barras_disponibles,
            self.desperdicios_disponibles,
            self.config_test
        )
        
        # Verificar que se retorna un cromosoma válido
        self.assertIsInstance(mejor_cromosoma, Cromosoma)
        self.assertGreater(len(mejor_cromosoma.patrones), 0)
        
        # Verificar estadísticas
        self.assertIsInstance(estadisticas, dict)
        self.assertIn('mejor_fitness_global', estadisticas)
        self.assertIn('generaciones_ejecutadas', estadisticas)
        self.assertIn('tiempo_total_segundos', estadisticas)
        
        # Verificar que se ejecutaron algunas generaciones
        self.assertGreater(estadisticas['generaciones_ejecutadas'], 0)
        self.assertLessEqual(estadisticas['generaciones_ejecutadas'], self.config_test['max_generaciones'])
    
    def test_ejecutar_algoritmo_genetico_simple(self):
        """Test de la versión simplificada del algoritmo genético."""
        mejor_cromosoma = ejecutar_algoritmo_genetico_simple(
            self.piezas_requeridas_df,
            self.barras_disponibles,
            self.desperdicios_disponibles,
            max_generaciones=3,
            tamaño_poblacion=4
        )
        
        self.assertIsInstance(mejor_cromosoma, Cromosoma)
        self.assertGreater(len(mejor_cromosoma.patrones), 0)
    
    def test_configuracion_por_defecto(self):
        """Test con configuración por defecto."""
        config_minima = {
            'max_generaciones': 3,
            'tamaño_poblacion': 4,
            'logging_habilitado': False
        }
        
        mejor_cromosoma, estadisticas = ejecutar_algoritmo_genetico(
            self.piezas_requeridas_df,
            self.barras_disponibles,
            self.desperdicios_disponibles,
            config_minima
        )
        
        self.assertIsInstance(mejor_cromosoma, Cromosoma)
        self.assertIsInstance(estadisticas, dict)
    
    def test_criterios_parada_max_generaciones(self):
        """Test del criterio de parada por máximo de generaciones."""
        config_ga = {'max_generaciones': 5}
        
        # Debería parar en la generación 5
        self.assertTrue(verificar_criterios_parada(5, [], time.time(), config_ga))
        
        # No debería parar antes
        self.assertFalse(verificar_criterios_parada(3, [], time.time(), config_ga))
    
    def test_criterios_parada_tiempo_limite(self):
        """Test del criterio de parada por tiempo límite."""
        config_ga = {'tiempo_limite_segundos': 1}
        tiempo_inicio = time.time() - 2  # Simular que han pasado 2 segundos
        
        self.assertTrue(verificar_criterios_parada(1, [], tiempo_inicio, config_ga))
    
    def test_criterios_parada_fitness_objetivo(self):
        """Test del criterio de parada por fitness objetivo."""
        config_ga = {'fitness_objetivo': 10.0}
        historial_fitness = [20.0, 15.0, 8.0]  # El último es mejor que el objetivo
        
        self.assertTrue(verificar_criterios_parada(3, historial_fitness, time.time(), config_ga))
        
        # No debería parar si no se alcanza el objetivo
        historial_fitness_alto = [20.0, 15.0, 12.0]
        self.assertFalse(verificar_criterios_parada(3, historial_fitness_alto, time.time(), config_ga))
    
    def test_aplicar_elitismo_sin_elitismo(self):
        """Test de reemplazo sin elitismo."""
        # Crear poblaciones de prueba
        poblacion_actual = self._crear_poblacion_prueba(4)
        valores_fitness_actual = [10.0, 8.0, 12.0, 6.0]
        
        poblacion_hijos = self._crear_poblacion_prueba(4)
        valores_fitness_hijos = [9.0, 7.0, 11.0, 5.0]
        
        config_ga = {'elitismo': False, 'tamaño_poblacion': 4}
        
        nueva_poblacion, nuevos_fitness = aplicar_elitismo_y_reemplazo(
            poblacion_actual,
            valores_fitness_actual,
            poblacion_hijos,
            valores_fitness_hijos,
            config_ga
        )
        
        # Sin elitismo, debería retornar exactamente los hijos
        self.assertEqual(len(nueva_poblacion), 4)
        self.assertEqual(nuevos_fitness, valores_fitness_hijos)
    
    def test_aplicar_elitismo_con_elitismo(self):
        """Test de reemplazo con elitismo."""
        poblacion_actual = self._crear_poblacion_prueba(4)
        valores_fitness_actual = [10.0, 8.0, 12.0, 6.0]  # Mejor: 6.0 (índice 3)
        
        poblacion_hijos = self._crear_poblacion_prueba(4)
        valores_fitness_hijos = [9.0, 7.0, 11.0, 8.5]  # Mejor: 7.0 (índice 1)
        
        config_ga = {
            'elitismo': True,
            'tamaño_elite': 1,
            'tamaño_poblacion': 4
        }
        
        nueva_poblacion, nuevos_fitness = aplicar_elitismo_y_reemplazo(
            poblacion_actual,
            valores_fitness_actual,
            poblacion_hijos,
            valores_fitness_hijos,
            config_ga
        )
        
        # Debería preservar el mejor de la población actual (fitness 6.0)
        self.assertEqual(len(nueva_poblacion), 4)
        self.assertIn(6.0, nuevos_fitness)  # El mejor de la élite debe estar presente
        self.assertEqual(min(nuevos_fitness), 6.0)  # El mejor global debe ser de la élite
    
    def test_validar_configuracion_ga_valida(self):
        """Test de validación con configuración válida."""
        config_valida = {
            'tamaño_poblacion': 10,
            'max_generaciones': 50,
            'tasa_cruce': 0.8,
            'tasa_mutacion_individuo': 0.2,
            'tasa_mutacion_gen': 0.1,
            'elitismo': True,
            'tamaño_elite': 2,
            'metodo_seleccion': 'torneo',
            'estrategia_cruce': 'un_punto'
        }
        
        errores = validar_configuracion_ga(config_valida)
        self.assertEqual(len(errores), 0)
    
    def test_validar_configuracion_ga_invalida(self):
        """Test de validación con configuración inválida."""
        config_invalida = {
            'tamaño_poblacion': 1,  # Muy pequeño
            'max_generaciones': 0,  # Muy pequeño
            'tasa_cruce': 1.5,  # Fuera de rango
            'tasa_mutacion_individuo': -0.1,  # Negativo
            'elitismo': True,
            'tamaño_elite': 10,  # Mayor que población
            'metodo_seleccion': 'inexistente',  # Método inválido
            'estrategia_cruce': 'inexistente'  # Estrategia inválida
        }
        
        errores = validar_configuracion_ga(config_invalida)
        self.assertGreater(len(errores), 0)
        
        # Verificar que se detectan errores específicos
        errores_str = ' '.join(errores)
        self.assertIn('población', errores_str)
        self.assertIn('generaciones', errores_str)
        self.assertIn('cruce', errores_str)
    
    def test_convergencia_por_generaciones_sin_mejora(self):
        """Test de convergencia por generaciones sin mejora."""
        config_convergencia = {
            **self.config_test,
            'criterio_convergencia': 'generaciones_sin_mejora',
            'generaciones_sin_mejora_max': 2,
            'max_generaciones': 10
        }
        
        mejor_cromosoma, estadisticas = ejecutar_algoritmo_genetico(
            self.piezas_requeridas_df,
            self.barras_disponibles,
            self.desperdicios_disponibles,
            config_convergencia
        )
        
        # Debería parar antes del máximo si converge
        self.assertIsInstance(mejor_cromosoma, Cromosoma)
        self.assertLessEqual(estadisticas['generaciones_ejecutadas'], 10)
    
    def test_diferentes_estrategias_inicializacion(self):
        """Test con diferentes estrategias de inicialización."""
        estrategias = ['heuristica', 'aleatoria', 'hibrida']
        
        for estrategia in estrategias:
            with self.subTest(estrategia=estrategia):
                config_estrategia = {
                    **self.config_test,
                    'estrategia_inicializacion': estrategia
                }
                
                mejor_cromosoma, estadisticas = ejecutar_algoritmo_genetico(
                    self.piezas_requeridas_df,
                    self.barras_disponibles,
                    self.desperdicios_disponibles,
                    config_estrategia
                )
                
                self.assertIsInstance(mejor_cromosoma, Cromosoma)
                self.assertGreater(len(mejor_cromosoma.patrones), 0)
    
    def test_diferentes_metodos_seleccion(self):
        """Test con diferentes métodos de selección."""
        metodos = ['torneo', 'ruleta', 'elitista']
        
        for metodo in metodos:
            with self.subTest(metodo=metodo):
                config_metodo = {
                    **self.config_test,
                    'metodo_seleccion': metodo
                }
                
                mejor_cromosoma, estadisticas = ejecutar_algoritmo_genetico(
                    self.piezas_requeridas_df,
                    self.barras_disponibles,
                    self.desperdicios_disponibles,
                    config_metodo
                )
                
                self.assertIsInstance(mejor_cromosoma, Cromosoma)
    
    def test_diferentes_estrategias_cruce(self):
        """Test con diferentes estrategias de cruce."""
        estrategias = ['un_punto', 'dos_puntos', 'basado_en_piezas']
        
        for estrategia in estrategias:
            with self.subTest(estrategia=estrategia):
                config_cruce = {
                    **self.config_test,
                    'estrategia_cruce': estrategia
                }
                
                mejor_cromosoma, estadisticas = ejecutar_algoritmo_genetico(
                    self.piezas_requeridas_df,
                    self.barras_disponibles,
                    self.desperdicios_disponibles,
                    config_cruce
                )
                
                self.assertIsInstance(mejor_cromosoma, Cromosoma)
    
    def test_manejo_errores(self):
        """Test de manejo de errores."""
        # Test con DataFrame vacío
        df_vacio = pd.DataFrame(columns=['id_pedido', 'longitud_pieza_requerida', 'cantidad_requerida'])
        
        with self.assertRaises(Exception):
            ejecutar_algoritmo_genetico(
                df_vacio,
                self.barras_disponibles,
                self.desperdicios_disponibles,
                self.config_test
            )
    
    def test_poblacion_pequena(self):
        """Test con población muy pequeña."""
        config_pequena = {
            **self.config_test,
            'tamaño_poblacion': 2,
            'tamaño_elite': 1
        }
        
        mejor_cromosoma, estadisticas = ejecutar_algoritmo_genetico(
            self.piezas_requeridas_df,
            self.barras_disponibles,
            self.desperdicios_disponibles,
            config_pequena
        )
        
        self.assertIsInstance(mejor_cromosoma, Cromosoma)
        # El algoritmo puede converger antes del máximo, así que verificamos que ejecutó al menos 1 generación
        self.assertGreater(estadisticas['generaciones_ejecutadas'], 0)
        self.assertLessEqual(estadisticas['generaciones_ejecutadas'], config_pequena['max_generaciones'])
    
    def _crear_poblacion_prueba(self, tamaño: int) -> list:
        """Crea una población de prueba con cromosomas simples."""
        poblacion = []
        for i in range(tamaño):
            patron = Patron(
                origen_barra_longitud=6.0,
                origen_barra_tipo='estandar',
                piezas_cortadas=[
                    {'id_pedido': f'P{i}', 'longitud_pieza': 2.0, 'cantidad_pieza_en_patron': 1}
                ]
            )
            cromosoma = Cromosoma([patron])
            poblacion.append(cromosoma)
        return poblacion


class TestRegistroEvolucion(unittest.TestCase):
    """Tests para el registro de evolución."""
    
    def test_registro_basico(self):
        """Test básico del registro de evolución."""
        registro = RegistroEvolucion()
        registro.iniciar_registro()
        
        # Crear datos de prueba
        poblacion = self._crear_poblacion_prueba(3)
        valores_fitness = [10.0, 8.0, 12.0]
        
        # Registrar una generación
        registro.registrar_generacion(1, poblacion, valores_fitness, 0.1)
        
        # Verificar que se registraron los datos
        self.assertEqual(len(registro.generaciones), 1)
        self.assertEqual(registro.mejor_fitness_por_generacion[0], 8.0)  # Menor es mejor
        self.assertEqual(registro.fitness_promedio_por_generacion[0], 10.0)
        
        registro.finalizar_registro()
        resumen = registro.obtener_resumen()
        
        self.assertEqual(resumen['mejor_fitness_global'], 8.0)
        self.assertEqual(resumen['generaciones_ejecutadas'], 1)
    
    def test_actualizacion_mejor_global(self):
        """Test de actualización del mejor fitness global."""
        registro = RegistroEvolucion()
        registro.iniciar_registro()
        
        poblacion = self._crear_poblacion_prueba(2)
        
        # Primera generación
        registro.registrar_generacion(1, poblacion, [10.0, 8.0], 0.1)
        self.assertEqual(registro.mejor_fitness_global, 8.0)
        
        # Segunda generación con mejora
        registro.registrar_generacion(2, poblacion, [7.0, 9.0], 0.1)
        self.assertEqual(registro.mejor_fitness_global, 7.0)
        self.assertEqual(registro.generacion_mejor_global, 2)
        
        # Tercera generación sin mejora
        registro.registrar_generacion(3, poblacion, [8.0, 10.0], 0.1)
        self.assertEqual(registro.mejor_fitness_global, 7.0)  # No debería cambiar
        self.assertEqual(registro.generacion_mejor_global, 2)  # No debería cambiar
    
    def _crear_poblacion_prueba(self, tamaño: int) -> list:
        """Crea una población de prueba."""
        poblacion = []
        for i in range(tamaño):
            patron = Patron(
                origen_barra_longitud=6.0,
                origen_barra_tipo='estandar',
                piezas_cortadas=[
                    {'id_pedido': f'P{i}', 'longitud_pieza': 2.0, 'cantidad_pieza_en_patron': 1}
                ]
            )
            cromosoma = Cromosoma([patron])
            poblacion.append(cromosoma)
        return poblacion


if __name__ == '__main__':
    unittest.main() 
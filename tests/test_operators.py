"""
Tests unitarios para los operadores genéticos.
"""

import unittest
import pandas as pd
import random

from genetic_algorithm.chromosome import Patron, Cromosoma
from genetic_algorithm.population import (
    inicializar_poblacion,
    generar_individuo_heuristico_ffd,
    generar_individuo_heuristico_bfd,
    generar_individuo_aleatorio_con_reparacion
)
from genetic_algorithm.selection import (
    seleccionar_padres,
    seleccion_torneo,
    seleccion_ruleta,
    seleccionar_parejas_para_cruce
)
from genetic_algorithm.crossover import (
    cruzar,
    cruce_un_punto,
    cruce_dos_puntos,
    cruce_basado_en_piezas
)
from genetic_algorithm.mutation import (
    mutar,
    mutacion_cambiar_origen_patron,
    mutacion_mover_pieza,
    mutacion_ajustar_cantidad_piezas
)
from genetic_algorithm.fitness import calcular_fitness


class TestPopulation(unittest.TestCase):
    """Tests para la inicialización de población."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.piezas_requeridas_df = pd.DataFrame([
            {'id_pedido': 'P001', 'longitud_pieza_requerida': 2.5, 'cantidad_requerida': 2},
            {'id_pedido': 'P002', 'longitud_pieza_requerida': 1.0, 'cantidad_requerida': 3},
            {'id_pedido': 'P003', 'longitud_pieza_requerida': 1.5, 'cantidad_requerida': 1}
        ])
        
        self.barras_disponibles = [
            {'longitud': 6.0, 'tipo': 'estandar'},
            {'longitud': 12.0, 'tipo': 'estandar'}
        ]
        
        self.desperdicios_disponibles = [
            {'longitud': 3.0, 'tipo': 'desperdicio'},
            {'longitud': 2.0, 'tipo': 'desperdicio'}
        ]
    
    def test_generar_individuo_ffd(self):
        """Test para la generación de individuo con FFD."""
        cromosoma = generar_individuo_heuristico_ffd(
            self.piezas_requeridas_df,
            self.barras_disponibles,
            self.desperdicios_disponibles
        )
        
        self.assertIsInstance(cromosoma, Cromosoma)
        self.assertGreater(len(cromosoma.patrones), 0)
        
        # Verificar que se generaron patrones válidos
        for patron in cromosoma.patrones:
            self.assertIsInstance(patron, Patron)
            self.assertGreater(len(patron.piezas_cortadas), 0)
    
    def test_generar_individuo_bfd(self):
        """Test para la generación de individuo con BFD."""
        cromosoma = generar_individuo_heuristico_bfd(
            self.piezas_requeridas_df,
            self.barras_disponibles,
            self.desperdicios_disponibles
        )
        
        self.assertIsInstance(cromosoma, Cromosoma)
        self.assertGreater(len(cromosoma.patrones), 0)
    
    def test_generar_individuo_aleatorio(self):
        """Test para la generación de individuo aleatorio."""
        cromosoma = generar_individuo_aleatorio_con_reparacion(
            self.piezas_requeridas_df,
            self.barras_disponibles,
            self.desperdicios_disponibles
        )
        
        self.assertIsInstance(cromosoma, Cromosoma)
        self.assertGreater(len(cromosoma.patrones), 0)
    
    def test_inicializar_poblacion_heuristica(self):
        """Test para inicialización de población heurística."""
        poblacion = inicializar_poblacion(
            tamaño_poblacion=10,
            piezas_requeridas_df=self.piezas_requeridas_df,
            barras_estandar_disponibles=self.barras_disponibles,
            desperdicios_reutilizables_previos=self.desperdicios_disponibles,
            estrategia_inicializacion='heuristica'
        )
        
        self.assertEqual(len(poblacion), 10)
        for cromosoma in poblacion:
            self.assertIsInstance(cromosoma, Cromosoma)
    
    def test_inicializar_poblacion_aleatoria(self):
        """Test para inicialización de población aleatoria."""
        poblacion = inicializar_poblacion(
            tamaño_poblacion=5,
            piezas_requeridas_df=self.piezas_requeridas_df,
            barras_estandar_disponibles=self.barras_disponibles,
            desperdicios_reutilizables_previos=self.desperdicios_disponibles,
            estrategia_inicializacion='aleatoria'
        )
        
        self.assertEqual(len(poblacion), 5)
        for cromosoma in poblacion:
            self.assertIsInstance(cromosoma, Cromosoma)
    
    def test_inicializar_poblacion_hibrida(self):
        """Test para inicialización de población híbrida."""
        poblacion = inicializar_poblacion(
            tamaño_poblacion=10,
            piezas_requeridas_df=self.piezas_requeridas_df,
            barras_estandar_disponibles=self.barras_disponibles,
            desperdicios_reutilizables_previos=self.desperdicios_disponibles,
            estrategia_inicializacion='hibrida',
            config_ga={'proporcion_heuristicos': 0.7}
        )
        
        self.assertEqual(len(poblacion), 10)
        for cromosoma in poblacion:
            self.assertIsInstance(cromosoma, Cromosoma)


class TestSelection(unittest.TestCase):
    """Tests para la selección de padres."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Crear una población de prueba
        self.poblacion = []
        for i in range(5):
            patron = Patron(
                origen_barra_longitud=6.0,
                origen_barra_tipo='estandar',
                piezas_cortadas=[
                    {'id_pedido': f'P{i}', 'longitud_pieza': 2.0, 'cantidad_pieza_en_patron': 1}
                ]
            )
            cromosoma = Cromosoma([patron])
            self.poblacion.append(cromosoma)
        
        # Valores de fitness (menor es mejor)
        self.valores_fitness = [10.0, 5.0, 15.0, 3.0, 8.0]
    
    def test_seleccion_torneo(self):
        """Test para selección por torneo."""
        padres = seleccion_torneo(
            self.poblacion,
            self.valores_fitness,
            num_padres=3,
            tamaño_torneo=2
        )
        
        self.assertEqual(len(padres), 3)
        for padre in padres:
            self.assertIsInstance(padre, Cromosoma)
    
    def test_seleccion_ruleta(self):
        """Test para selección por ruleta."""
        padres = seleccion_ruleta(
            self.poblacion,
            self.valores_fitness,
            num_padres=3
        )
        
        self.assertEqual(len(padres), 3)
        for padre in padres:
            self.assertIsInstance(padre, Cromosoma)
    
    def test_seleccionar_padres_torneo(self):
        """Test para la función principal de selección con torneo."""
        padres = seleccionar_padres(
            self.poblacion,
            self.valores_fitness,
            numero_de_padres_a_seleccionar=4,
            metodo_seleccion='torneo',
            tamaño_torneo=3
        )
        
        self.assertEqual(len(padres), 4)
    
    def test_seleccionar_padres_ruleta(self):
        """Test para la función principal de selección con ruleta."""
        padres = seleccionar_padres(
            self.poblacion,
            self.valores_fitness,
            numero_de_padres_a_seleccionar=3,
            metodo_seleccion='ruleta'
        )
        
        self.assertEqual(len(padres), 3)
    
    def test_seleccionar_parejas(self):
        """Test para formar parejas de padres."""
        padres = seleccionar_padres(
            self.poblacion,
            self.valores_fitness,
            numero_de_padres_a_seleccionar=4,
            metodo_seleccion='torneo'
        )
        
        parejas = seleccionar_parejas_para_cruce(padres, 'aleatorio')
        
        self.assertEqual(len(parejas), 2)  # 4 padres = 2 parejas
        for pareja in parejas:
            self.assertEqual(len(pareja), 2)
            self.assertIsInstance(pareja[0], Cromosoma)
            self.assertIsInstance(pareja[1], Cromosoma)


class TestCrossover(unittest.TestCase):
    """Tests para el operador de cruce."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.piezas_requeridas_df = pd.DataFrame([
            {'id_pedido': 'P001', 'longitud_pieza_requerida': 2.0, 'cantidad_requerida': 2},
            {'id_pedido': 'P002', 'longitud_pieza_requerida': 1.5, 'cantidad_requerida': 2}
        ])
        
        # Crear cromosomas padre de prueba
        patron1 = Patron(
            origen_barra_longitud=6.0,
            origen_barra_tipo='estandar',
            piezas_cortadas=[
                {'id_pedido': 'P001', 'longitud_pieza': 2.0, 'cantidad_pieza_en_patron': 2}
            ]
        )
        
        patron2 = Patron(
            origen_barra_longitud=4.0,
            origen_barra_tipo='estandar',
            piezas_cortadas=[
                {'id_pedido': 'P002', 'longitud_pieza': 1.5, 'cantidad_pieza_en_patron': 2}
            ]
        )
        
        self.padre1 = Cromosoma([patron1])
        self.padre2 = Cromosoma([patron2])
    
    def test_cruce_un_punto(self):
        """Test para cruce de un punto."""
        hijo1, hijo2 = cruce_un_punto(self.padre1, self.padre2, self.piezas_requeridas_df)
        
        self.assertIsInstance(hijo1, Cromosoma)
        self.assertIsInstance(hijo2, Cromosoma)
        self.assertGreater(len(hijo1.patrones), 0)
        self.assertGreater(len(hijo2.patrones), 0)
    
    def test_cruce_dos_puntos(self):
        """Test para cruce de dos puntos."""
        hijo1, hijo2 = cruce_dos_puntos(self.padre1, self.padre2, self.piezas_requeridas_df)
        
        self.assertIsInstance(hijo1, Cromosoma)
        self.assertIsInstance(hijo2, Cromosoma)
    
    def test_cruce_basado_en_piezas(self):
        """Test para cruce basado en piezas."""
        hijo1, hijo2 = cruce_basado_en_piezas(self.padre1, self.padre2, self.piezas_requeridas_df)
        
        self.assertIsInstance(hijo1, Cromosoma)
        self.assertIsInstance(hijo2, Cromosoma)
    
    def test_cruzar_con_tasa_baja(self):
        """Test para cruce con tasa baja (no debería ocurrir cruce)."""
        # Fijar semilla para resultado predecible
        random.seed(42)
        
        hijo1, hijo2 = cruzar(
            self.padre1,
            self.padre2,
            self.piezas_requeridas_df,
            tasa_cruce=0.0,  # Tasa muy baja
            estrategia_cruce='un_punto'
        )
        
        # Con tasa 0.0, deberían ser copias de los padres
        self.assertEqual(len(hijo1.patrones), len(self.padre1.patrones))
        self.assertEqual(len(hijo2.patrones), len(self.padre2.patrones))
    
    def test_cruzar_con_tasa_alta(self):
        """Test para cruce con tasa alta (debería ocurrir cruce)."""
        hijo1, hijo2 = cruzar(
            self.padre1,
            self.padre2,
            self.piezas_requeridas_df,
            tasa_cruce=1.0,  # Tasa máxima
            estrategia_cruce='un_punto'
        )
        
        self.assertIsInstance(hijo1, Cromosoma)
        self.assertIsInstance(hijo2, Cromosoma)


class TestMutation(unittest.TestCase):
    """Tests para el operador de mutación."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.piezas_requeridas_df = pd.DataFrame([
            {'id_pedido': 'P001', 'longitud_pieza_requerida': 2.0, 'cantidad_requerida': 2},
            {'id_pedido': 'P002', 'longitud_pieza_requerida': 1.5, 'cantidad_requerida': 2}
        ])
        
        self.barras_disponibles = [
            {'longitud': 6.0, 'tipo': 'estandar'},
            {'longitud': 8.0, 'tipo': 'estandar'}
        ]
        
        self.desperdicios_disponibles = [
            {'longitud': 3.0, 'tipo': 'desperdicio'}
        ]
        
        # Crear cromosoma de prueba
        patron1 = Patron(
            origen_barra_longitud=6.0,
            origen_barra_tipo='estandar',
            piezas_cortadas=[
                {'id_pedido': 'P001', 'longitud_pieza': 2.0, 'cantidad_pieza_en_patron': 1},
                {'id_pedido': 'P002', 'longitud_pieza': 1.5, 'cantidad_pieza_en_patron': 1}
            ]
        )
        
        patron2 = Patron(
            origen_barra_longitud=4.0,
            origen_barra_tipo='estandar',
            piezas_cortadas=[
                {'id_pedido': 'P001', 'longitud_pieza': 2.0, 'cantidad_pieza_en_patron': 1}
            ]
        )
        
        self.cromosoma = Cromosoma([patron1, patron2])
    
    def test_mutacion_cambiar_origen(self):
        """Test para mutación de cambio de origen."""
        cromosoma_copia = Cromosoma([p for p in self.cromosoma.patrones])
        
        exito = mutacion_cambiar_origen_patron(
            cromosoma_copia,
            indice_patron=0,
            nuevas_barras_disponibles=self.barras_disponibles
        )
        
        # La mutación debería ser exitosa
        self.assertTrue(exito)
    
    def test_mutacion_mover_pieza(self):
        """Test para mutación de mover pieza."""
        cromosoma_copia = Cromosoma([p for p in self.cromosoma.patrones])
        
        pieza_info = {
            'id_pedido': 'P002',
            'longitud_pieza': 1.5
        }
        
        exito = mutacion_mover_pieza(
            cromosoma_copia,
            patron_origen=0,
            patron_destino=1,
            pieza_info=pieza_info
        )
        
        # La mutación debería ser exitosa
        self.assertTrue(exito)
    
    def test_mutacion_ajustar_cantidad(self):
        """Test para mutación de ajustar cantidad."""
        cromosoma_copia = Cromosoma([p for p in self.cromosoma.patrones])
        
        # Esta mutación puede o no ser exitosa dependiendo del estado del cromosoma
        exito = mutacion_ajustar_cantidad_piezas(
            cromosoma_copia,
            self.piezas_requeridas_df
        )
        
        # Verificar que el cromosoma sigue siendo válido
        self.assertIsInstance(cromosoma_copia, Cromosoma)
    
    def test_mutar_con_tasa_baja(self):
        """Test para mutación con tasa baja."""
        cromosoma_mutado = mutar(
            self.cromosoma,
            self.piezas_requeridas_df,
            self.barras_disponibles,
            self.desperdicios_disponibles,
            tasa_mutacion_individuo=0.0,  # Tasa muy baja
            tasa_mutacion_gen=0.1
        )
        
        # Con tasa 0.0, debería retornar el mismo cromosoma
        self.assertEqual(id(cromosoma_mutado), id(self.cromosoma))
    
    def test_mutar_con_tasa_alta(self):
        """Test para mutación con tasa alta."""
        cromosoma_mutado = mutar(
            self.cromosoma,
            self.piezas_requeridas_df,
            self.barras_disponibles,
            self.desperdicios_disponibles,
            tasa_mutacion_individuo=1.0,  # Tasa máxima
            tasa_mutacion_gen=0.5,
            config_ga={'operaciones_mutacion': ['cambiar_origen']}
        )
        
        # Debería retornar un cromosoma diferente (copia mutada)
        self.assertNotEqual(id(cromosoma_mutado), id(self.cromosoma))
        self.assertIsInstance(cromosoma_mutado, Cromosoma)


class TestIntegracionOperadores(unittest.TestCase):
    """Tests de integración para todos los operadores."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.piezas_requeridas_df = pd.DataFrame([
            {'id_pedido': 'P001', 'longitud_pieza_requerida': 2.5, 'cantidad_requerida': 2},
            {'id_pedido': 'P002', 'longitud_pieza_requerida': 1.0, 'cantidad_requerida': 3}
        ])
        
        self.barras_disponibles = [
            {'longitud': 6.0, 'tipo': 'estandar'},
            {'longitud': 12.0, 'tipo': 'estandar'}
        ]
        
        self.desperdicios_disponibles = [
            {'longitud': 3.0, 'tipo': 'desperdicio'}
        ]
    
    def test_flujo_completo_operadores(self):
        """Test del flujo completo de operadores genéticos."""
        # 1. Inicializar población
        poblacion = inicializar_poblacion(
            tamaño_poblacion=6,
            piezas_requeridas_df=self.piezas_requeridas_df,
            barras_estandar_disponibles=self.barras_disponibles,
            desperdicios_reutilizables_previos=self.desperdicios_disponibles,
            estrategia_inicializacion='hibrida'
        )
        
        self.assertEqual(len(poblacion), 6)
        
        # 2. Calcular fitness
        valores_fitness = []
        for cromosoma in poblacion:
            fitness = calcular_fitness(cromosoma, self.piezas_requeridas_df)
            valores_fitness.append(fitness)
        
        self.assertEqual(len(valores_fitness), 6)
        
        # 3. Seleccionar padres
        padres = seleccionar_padres(
            poblacion,
            valores_fitness,
            numero_de_padres_a_seleccionar=4,
            metodo_seleccion='torneo',
            tamaño_torneo=2
        )
        
        self.assertEqual(len(padres), 4)
        
        # 4. Formar parejas
        parejas = seleccionar_parejas_para_cruce(padres, 'aleatorio')
        self.assertEqual(len(parejas), 2)
        
        # 5. Realizar cruce
        hijos = []
        for padre1, padre2 in parejas:
            hijo1, hijo2 = cruzar(
                padre1,
                padre2,
                self.piezas_requeridas_df,
                tasa_cruce=0.8,
                estrategia_cruce='un_punto'
            )
            hijos.extend([hijo1, hijo2])
        
        self.assertEqual(len(hijos), 4)
        
        # 6. Aplicar mutación
        hijos_mutados = []
        for hijo in hijos:
            hijo_mutado = mutar(
                hijo,
                self.piezas_requeridas_df,
                self.barras_disponibles,
                self.desperdicios_disponibles,
                tasa_mutacion_individuo=0.3,
                tasa_mutacion_gen=0.1
            )
            hijos_mutados.append(hijo_mutado)
        
        self.assertEqual(len(hijos_mutados), 4)
        
        # Verificar que todos los hijos son cromosomas válidos
        for hijo in hijos_mutados:
            self.assertIsInstance(hijo, Cromosoma)
            self.assertGreater(len(hijo.patrones), 0)


if __name__ == '__main__':
    unittest.main() 
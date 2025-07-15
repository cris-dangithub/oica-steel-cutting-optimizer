"""
Módulo para la representación del cromosoma en el algoritmo genético.

Este módulo define las estructuras de datos básicas para representar soluciones 
al problema de corte de acero en el algoritmo genético.
"""

from typing import List, Dict, Any, Union, Optional
from copy import deepcopy
from . import LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE

class Patron:
    """
    Representa un patrón de corte para una barra específica.
    
    Un patrón define cómo se corta una barra de origen (estándar o desperdicio)
    en piezas específicas, registrando las piezas cortadas y el desperdicio resultante.
    """
    
    def __init__(
        self, 
        origen_barra_longitud: float, 
        origen_barra_tipo: str,
        piezas_cortadas: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Inicializa un nuevo patrón de corte.
        
        Args:
            origen_barra_longitud: Longitud de la barra de origen en metros.
            origen_barra_tipo: Tipo de barra ('estandar' o 'desperdicio').
            piezas_cortadas: Lista de diccionarios que representan las piezas cortadas.
                Cada pieza tiene formato {'id_pedido': id, 'longitud_pieza': longitud, 'cantidad_pieza_en_patron': cantidad}
                Si no se proporciona, se inicializa como una lista vacía.
        """
        self.origen_barra_longitud = origen_barra_longitud
        self.origen_barra_tipo = origen_barra_tipo
        self.piezas_cortadas = piezas_cortadas or []
        
        # Calcular el desperdicio y determinar si es utilizable
        self._calcular_desperdicio()
        
    def _calcular_desperdicio(self) -> None:
        """
        Calcula el desperdicio resultante y determina si es utilizable.
        
        El desperdicio es la longitud de la barra origen menos la suma de las longitudes
        de todas las piezas cortadas multiplicadas por sus cantidades respectivas.
        """
        longitud_total_utilizada = sum(
            pieza['longitud_pieza'] * pieza['cantidad_pieza_en_patron']
            for pieza in self.piezas_cortadas
        )
        
        self.desperdicio_patron_longitud = round(self.origen_barra_longitud - longitud_total_utilizada, 3)
        self.es_desperdicio_utilizable = self.desperdicio_patron_longitud >= LONGITUD_MINIMA_DESPERDICIO_UTILIZABLE
    
    def agregar_pieza(self, id_pedido: Any, longitud_pieza: float, cantidad: int = 1) -> bool:
        """
        Agrega una pieza al patrón si hay espacio suficiente.
        
        Args:
            id_pedido: Identificador único del pedido.
            longitud_pieza: Longitud de la pieza a cortar en metros.
            cantidad: Número de piezas de este tipo a agregar (por defecto 1).
            
        Returns:
            bool: True si la pieza se agregó correctamente, False si no hay espacio suficiente.
        """
        # Verificar si hay espacio suficiente para la pieza
        longitud_necesaria = longitud_pieza * cantidad
        if longitud_necesaria > self.desperdicio_patron_longitud:
            return False
        
        # Agregar la pieza al patrón
        self.piezas_cortadas.append({
            'id_pedido': id_pedido,
            'longitud_pieza': longitud_pieza,
            'cantidad_pieza_en_patron': cantidad
        })
        
        # Recalcular el desperdicio
        self._calcular_desperdicio()
        return True
    
    def obtener_longitud_utilizada(self) -> float:
        """
        Retorna la longitud total utilizada por todas las piezas en el patrón.
        
        Returns:
            float: Suma de las longitudes de todas las piezas cortadas.
        """
        return self.origen_barra_longitud - self.desperdicio_patron_longitud
    
    def es_valido(self) -> bool:
        """
        Verifica si el patrón es válido (no excede la longitud de la barra origen).
        
        Returns:
            bool: True si el patrón es válido, False en caso contrario.
        """
        return self.desperdicio_patron_longitud >= 0
    
    def __str__(self) -> str:
        """Representación en string del patrón."""
        piezas_str = ', '.join([
            f"{p['cantidad_pieza_en_patron']}x{p['longitud_pieza']}m (Pedido: {p['id_pedido']})"
            for p in self.piezas_cortadas
        ])
        return (f"Patrón: Barra {self.origen_barra_tipo} de {self.origen_barra_longitud}m → "
                f"Piezas: [{piezas_str}], "
                f"Desperdicio: {self.desperdicio_patron_longitud}m "
                f"({'Utilizable' if self.es_desperdicio_utilizable else 'No utilizable'})")
    
    def __repr__(self) -> str:
        """Representación detallada del patrón."""
        return self.__str__()


class Cromosoma:
    """
    Representa una solución completa al problema de corte de acero para un subproblema específico.
    
    Un cromosoma contiene una lista de patrones de corte que, en conjunto, deben satisfacer
    la demanda de piezas requeridas para un número de barra y grupo de ejecución específicos.
    """
    
    def __init__(self, patrones: Optional[List[Patron]] = None):
        """
        Inicializa un nuevo cromosoma.
        
        Args:
            patrones: Lista de objetos Patron que conforman la solución.
                Si no se proporciona, se inicializa como una lista vacía.
        """
        self.patrones = patrones or []
    
    def agregar_patron(self, patron: Patron) -> None:
        """
        Agrega un patrón al cromosoma.
        
        Args:
            patron: Objeto Patron a agregar.
        """
        self.patrones.append(patron)
    
    def calcular_desperdicio_total(self) -> float:
        """
        Calcula el desperdicio total generado por todos los patrones del cromosoma.
        
        Returns:
            float: Suma de los desperdicios de todos los patrones.
        """
        return sum(patron.desperdicio_patron_longitud for patron in self.patrones)
    
    def obtener_desperdicios_utilizables(self) -> List[float]:
        """
        Retorna una lista con las longitudes de los desperdicios utilizables.
        
        Returns:
            List[float]: Lista de longitudes de desperdicios utilizables.
        """
        return [
            patron.desperdicio_patron_longitud 
            for patron in self.patrones 
            if patron.es_desperdicio_utilizable
        ]
    
    def contar_barras_estandar(self) -> int:
        """
        Cuenta el número de barras estándar utilizadas en el cromosoma.
        
        Returns:
            int: Número de patrones que usan barras estándar.
        """
        return sum(1 for patron in self.patrones if patron.origen_barra_tipo == 'estandar')
    
    def contar_desperdicios_usados(self) -> int:
        """
        Cuenta el número de desperdicios utilizados como origen en el cromosoma.
        
        Returns:
            int: Número de patrones que usan desperdicios como origen.
        """
        return sum(1 for patron in self.patrones if patron.origen_barra_tipo == 'desperdicio')
    
    def longitud_total_desperdicios_usados(self) -> float:
        """
        Calcula la longitud total de desperdicios utilizados como barras origen.
        
        Returns:
            float: Suma de las longitudes de desperdicios utilizados.
        """
        return sum(
            patron.origen_barra_longitud 
            for patron in self.patrones 
            if patron.origen_barra_tipo == 'desperdicio'
        )
    
    def clonar(self) -> 'Cromosoma':
        """
        Crea una copia profunda del cromosoma.
        
        Returns:
            Cromosoma: Una nueva instancia que es copia del cromosoma actual.
        """
        return deepcopy(self)
    
    def __len__(self) -> int:
        """Retorna el número de patrones en el cromosoma."""
        return len(self.patrones)
    
    def __str__(self) -> str:
        """Representación en string del cromosoma."""
        return f"Cromosoma con {len(self.patrones)} patrones, desperdicio total: {self.calcular_desperdicio_total():.2f}m"
    
    def __repr__(self) -> str:
        """Representación detallada del cromosoma."""
        return f"Cromosoma(patrones={self.patrones})" 
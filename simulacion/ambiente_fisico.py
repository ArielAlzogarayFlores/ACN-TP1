# Para representar el espacio físico del avión como una matriz usamos numpy
import numpy as np

# Para lidiar con probabilidades y aleatoriedad usamos este módulo
import random

# Importamos el agente de nuestro modelo, el pasajero
from agente import PassengerAgent

# El ambiente de nuestro modelo es el avión
class PlaneModel:
    '''
    Para seleccionar el método de llenado, se tienen cuatro opciones:
    - 'btf' para la política Back-to-Front.
    - 'rand' para la política aleatoria.
    - 'wilma' para la política Window-Middle-Aisle.
    - 'stfn' para el método de Steffen.
    '''

    # Método constructor de la clase avión
    # n es la cantidad de pasajeros, p la probabilidad de que un pasajero tenga
    # equipaje de mano y onboarding_method la política de embarque a utilizar
    def __init__(self, n=100, p=0.5, onboarding_method='rand'):

        # Atributos de la clase avión

        # Indica la fila (cola) de asientos en el orden en que embarcan los
        # pasajeros, el primer asiento de la lista es el del primero en subir
        self.queue: list[tuple[int, int]] = list()

        # Indica el espacio físico del avión: 25 filas y 5 columnas, donde la
        # columna 2 es el pasillo y las columnas 0, 1, 3 y 4 son los asientos
        # (0 y 4 ventana, 1 y 3 pasillo). Cada celda vale 1 si está ocupada
        # por un pasajero y 0 si está libre
        self.plane_grid: np.ndarray = np.zeros((25, 5))

        # Indica el reloj global de la simulación (en segundos)
        self.time: int = 0

        # Indica qué pasajero tiene asignado cada asiento, para que un
        # pasajero pueda encontrar al que está sentado en su camino y pedirle
        # que se levante
        self.passenger_at_seat: dict[tuple[int, int], PassengerAgent] = dict()

        # Generamos la cola de embarque según la política elegida

        # Back-to-Front y aleatoria: partimos de todos los asientos mezclados
        if onboarding_method == 'btf' or onboarding_method == 'rand':

            # Agregamos todos los asientos (salteando la columna del pasillo)
            for row in range(25):
                for col in range(5):
                    if (col != 2):
                        self.queue.append((row, col))

            # Los mezclamos, con esto ya queda armada la política aleatoria
            random.shuffle(self.queue)

            # Para Back-to-Front ordenamos de la última fila a la primera
            # Dentro de una misma fila se mantiene el orden aleatorio de la mezcla
            if onboarding_method == 'btf':
                self.queue.sort(key=lambda tup: tup[0], reverse=True)

        # Window-Middle-Aisle: primero ventanas, después el resto
        elif onboarding_method == 'wilma':

            # Agregamos todos los asientos (salteando la columna del pasillo)
            for row in range(25):
                for col in range(5):
                    if (col != 2):
                        self.queue.append((row, col))

            # Los mezclamos para que dentro de cada grupo el orden sea aleatorio
            random.shuffle(self.queue)

            # Ponemos primero las columnas pares (0 y 4, ventana) y después las
            # impares (1 y 3, pasillo) así que queda ventana primero y pasillo después
            self.queue.sort(key=lambda tup: tup[1] % 2 == 0, reverse=True)

        # Método de Steffen: ventanas primero, de atrás hacia adelante y
        # salteando una fila por medio, para que los pasajeros que guardan
        # equipaje al mismo tiempo no se estorben 
        elif onboarding_method == 'stfn':

            # Ventanas de las filas pares, de atrás hacia adelante
            # (primero todo el lado izquierdo, después todo el derecho)
            for col in [0, 4]:
                for row in range(24, -1, -2):
                    self.queue.append((row, col))

            # Ventanas de las filas impares, de atrás hacia adelante
            for col in [0, 4]:
                for row in range(23, 0, -2):
                    self.queue.append((row, col))

            # Asientos de pasillo de las filas pares, de atrás hacia adelante
            for col in [1, 3]:
                for row in range(24, -1, -2):
                    self.queue.append((row, col))

            # Asientos de pasillo de las filas impares, de atrás hacia adelante
            for col in [1, 3]:
                for row in range(23, 0, -2):
                    self.queue.append((row, col))

        # Si la política no es ninguna de las anteriores no podemos simular
        else:
            raise ValueError(f"Método de embarque inválido: {onboarding_method!r}")

        # Por si tenemos menos pasajeros que asientos, nos quedamos solo con
        # los primeros n asientos de la cola
        self.queue = self.queue[:n]

        # Indica la lista de agentes pasajeros, en el mismo orden que la cola
        self.agents: list[PassengerAgent] = list()

        # Creamos un pasajero por cada asiento de la cola
        for seat in self.queue:
            # Con probabilidad p el pasajero tiene equipaje de mano
            carryon = bool(random.choices([0, 1], weights=[1 - p, p])[0])
            pasajero = PassengerAgent(seat=seat, carryon=carryon, plane=self)
            self.agents.append(pasajero)
            self.passenger_at_seat[seat] = pasajero

    # Método para saber si una celda del avión está ocupada por algún pasajero
    def is_cell_occupied(self, cell: tuple[int, int]):
        return self.plane_grid[cell] == 1

    # Método para saber si terminó el embarque, es decir, si todos los
    # pasajeros están sentados. Usamos el estado 'seated' (y no arrived_at_seat)
    # para no dar por terminado el embarque mientras alguien está parado
    # dejando pasar a otro pasajero
    def all_passengers_seated(self):
        res:bool = False
        n_passengers_seated:int = 0
        for passenger in self.agents:
            if passenger.state == 'seated': n_passengers_seated += 1
        if n_passengers_seated == len(self.queue): res = True
        return res

    # Método que avanza la simulación un segundo
    def step(self):

        # Primero se activan los pasajeros que todavía no lo estaban.
        # Como se activan todos en el primer paso, todos quedan esperando
        # en la puerta y van entrando a medida que la celda (0, 2) se libera
        for agent in self.agents:
            agent.activate()

        # Después cada pasajero realiza la acción que le corresponde según su
        # estado. El orden importa: los que están más adelante en la cola
        # actúan primero, así si uno avanza, el de atrás puede ocupar la celda
        # que dejó libre en ese mismo segundo
        for agent in self.agents:
            agent.orchestrator()

        # Finalmente avanza el reloj global
        self.time += 1
import numpy as np
import random
from agente import PassengerAgent

class PlaneModel:
    '''
    Para seleccionar el método de llenado, se tienen cuatro opciones:
    - 'btf' para la política Back-to-Front.
    - 'rand' para la política aleatoria.
    - 'wilma' para la política Window-Middle-Aisle.
    - 'stfn' para el método de Steffen.
    '''
 
    def __init__(self, n=100, p=0.5, onboarding_method='rand'):
        self.queue: list[tuple[int, int]] = list()
 
        # Espacio físico
        self.plane_grid: np.ndarray = np.zeros((25, 5))
 
        # Reloj global
        self.time: int = 0
 
        # Asiento-pasajero
        self.passenger_at_seat: dict[tuple[int, int], Passenger] = dict()  # type: ignore
 
        # Generemos la queue
        if onboarding_method == 'btf' or onboarding_method == 'rand':
 
            for row in range(25):
                for col in range(5):
                    if (col != 2):
                        self.queue.append((row, col))
 
            random.shuffle(self.queue)
 
            if onboarding_method == 'btf':
                self.queue.sort(key=lambda tup: tup[0], reverse=True)
 
        elif onboarding_method == 'wilma':
 
            for row in range(25):
                for col in range(5):
                    if (col != 2):
                        self.queue.append((row, col))
 
            random.shuffle(self.queue)
            self.queue.sort(key=lambda tup: tup[1] % 2 == 0, reverse=True)
 
        elif onboarding_method == 'stfn':
 
            for col in [0, 4]:
                for row in range(24, -1, -2):
                    self.queue.append((row, col))
 
            for col in [0, 4]:
                for row in range(23, 0, -2):
                    self.queue.append((row, col))
 
            for col in [1, 3]:
                for row in range(24, -1, -2):
                    self.queue.append((row, col))
 
            for col in [1, 3]:
                for row in range(23, 0, -2):
                    self.queue.append((row, col))
 
        else:
            raise ValueError(f"Método de embarque inválido: {onboarding_method!r}")
 
        # Por si tenemos menos pasajeros que asientos
        self.queue = self.queue[:n]
 
        # Creamos lista de agentes
        self.agents: list[PassengerAgent] = list()
        for seat in self.queue:
            carryon = bool(random.choices([0, 1], weights=[p, 1 - p])[0])
            pasajero = PassengerAgent(seat=seat, carryon=carryon, plane=self)
            self.agents.append(pasajero)  # type: ignore
            self.passenger_at_seat[seat] = pasajero
 
    def is_cell_occupied(self, cell: tuple[int, int]):
        return self.plane_grid[cell] == 1

    def step(self):
        for agent in self.agents:
            agent.activate()
        for agent in self.agents:
            agent.orchestrator()
        self.time += 1

    def all_passengers_seated(self):
        res:bool = False
        n_passengers_seated:int = 0
        for passenger in self.agents:
            if passenger.state == 'seated': n_passengers_seated += 1
        if n_passengers_seated == len(self.queue): res = True
        return res
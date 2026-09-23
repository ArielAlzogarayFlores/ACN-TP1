'''
Idea bonus: heterogeneidad en velocidad de los pasajeros
---
En la realidad, no todos los pasajeros tardan lo mismo en moverse en la fila
del avion. La velocidad a la que avanza la fila esta limitada
por la velocidad de la persona mas lenta, ya que esto puede
generar acumulacion de personas en la fila.

En el codigo principal (base), asumimos que todos los pasajeros se mueven
a la misma velocidad.

En esta parte de nuestro trabajo, introducimos ciertos parametros que
van a determinar la velocidad de cada pasajero. Los parametros responden al grupo al
que pertenece el pasajero.
'''

# Para poder usar el tipo `PlaneModel` sin tener problemas con el interprete
from __future__ import annotations

# Para lidiar con probabilidades y aleatoriedad usamos este módulo
import random

# Constantes de utilidad que nos indican el rango apróximado que demora un
# pasajero promedio en realizar cada acción (en segundos)
STORE_CARRYON_MIN = 12
STORE_CARRYON_MAX = 32

SIT_MIN = 4
SIT_MAX = 12

GET_UP_MIN = 3
GET_UP_MAX = 5

# El agente de nuestro modelo es el pasajero
class BonusPassengerAgent:

    # Método constructor de la clase pasajero
    # seat es el asiento del pasajero, carryon indica si tiene equipaje de mano
    # y plane refiere al avión al que debe abordar
    def __init__(self, seat: tuple[int, int], carryon: bool, plane: PlaneModel):  # type: ignore

        # Atributos base de la clase pasajero
        self.seat: tuple[int, int] = seat
        self.carryon: bool = carryon
        self.arrived_at_seat: bool = False
        self.is_active = False
        self.cell: tuple[int, int] | None = None
        self.plane = plane

        # Estados posibles:
        # 'walking' -> avanza por el pasillo/la fila
        # 'storing_carryon' -> guarda el equipaje
        # 'sitting' -> se está sentando
        # 'seated' -> sentado
        # 'getting_up' -> se está parando para dejar pasar
        # 'exchanging_positions' -> ya de pie, espera a que el otro pase
        self.state: str = 'walking'

        self.waiting_timer: int = 0

        if carryon == True:
            self.carryon_stored: bool | None = False
        else:
            self.carryon_stored: bool | None = None

        # Asignamos condiciones con probabilidades realistas.
        # 'is_disabled' -> el pasajero tiene alguna discapacidad
        # 'is_elderly' -> el pasajero tiene 60+ 
        # 'is_pregnant' -> el pasajero es una embarazada
        # Un pasajero no puede ser una embarazada y tener 60+

        self.is_elderly = random.random() <= 0.15   
        self.is_pregnant = (not self.is_elderly) and (random.random() <= 0.04)  
        self.is_disabled = random.random() <= 0.02  

        # Generamos los tiempos base del pasajero
        self.walk_delay = random.randint(2, 4)
        self.store_delay = random.randint(STORE_CARRYON_MIN, STORE_CARRYON_MAX)
        self.sit_delay = random.randint(SIT_MIN, SIT_MAX)
        self.get_up_delay = random.randint(GET_UP_MIN, GET_UP_MAX)

        # Aplicamos penalidades según condiciones
        if self.is_disabled:
            self.walk_delay += 4
            self.sit_delay += 8
            self.get_up_delay += 6
            if self.carryon:
                self.store_delay += 20

        if self.is_elderly:
            self.walk_delay += 2
            if self.carryon:
                self.store_delay += 10

        if self.is_pregnant:
            self.sit_delay += 5
            self.get_up_delay += 4
            if self.carryon:
                self.store_delay += 15

        # Caminar con carry-on es más lento
        if self.carryon and not (self.is_disabled or self.is_elderly or self.is_pregnant):
            self.walk_delay += 1

        self.timer: int = self.walk_delay


    # Método de activación del agente pasajero
    # Marca el ingreso del pasajero al avión (aún sin posición asignada en el avión)
    def activate(self):
        if self.is_active:
            return
        self.is_active = True
        # print(f"Agente del asiento {self.seat} ingresa al avión en el momento t={self.plane.time} segundos.")

    # Método orquestrador
    def orchestrator(self):
        if not self.is_active:
            return

        if self.state == 'walking':
            self.walk_forward()

        elif self.state == 'storing_carryon':
            self.store_carryon()

        elif self.state == 'sitting':
            self.sit_down()

        elif self.state == 'getting_up':
            self.get_up()

        elif self.state == 'exchanging_positions':
            self.exchange_positions()

    # Método para guardar equipaje de mano
    def store_carryon(self):
        self.timer -= 1
        if self.timer == 0:
            self.carryon_stored = True
            self.state = 'walking'
            # Reasignamos su velocidad de caminata personal para retomar la marcha
            self.timer = self.walk_delay

    # Método para sentarse
    def sit_down(self):
        self.timer -= 1
        if self.timer == 0:
            self.state = 'seated'
            self.arrived_at_seat = True
            print(f"Agente del asiento {self.seat} se sienta en el momento t={self.plane.time} segundos.")

    # Método para pedirle a un pasajero que se levante de su asiento
    def receive_get_up_request(self):
        if self.state != 'seated':
            return
        self.state = 'getting_up'
        # Usa su tiempo personal para pararse
        self.timer = self.get_up_delay
        # print(f"Agente del asiento {self.seat} se levanta para dejar pasar en el momento t={self.plane.time} segundos.")

    # Método para levantarse de su asiento
    def get_up(self):
        self.timer -= 1
        if self.timer == 0:
            self.plane.plane_grid[self.seat] = 0
            self.state = 'exchanging_positions'

    # Método de intercambio de posiciones entre dos pasajeros
    def exchange_positions(self):
        if self.plane.plane_grid[self.seat] == 0:
            self.plane.plane_grid[self.seat] = 1
            self.state = 'seated'
            print(f"Agente del asiento {self.seat} se vuelve a sentar en el momento t={self.plane.time} segundos.")

    # Método para avanzar hacia el asiento
    def walk_forward(self):
        if self.cell == None:
            next_cell = (0, 2)
        else:
            cell_row, cell_col = self.cell
            seat_row, seat_col = self.seat

            if cell_row < seat_row:
                next_cell = (cell_row + 1, cell_col)
            elif cell_col == 2 and self.carryon and not self.carryon_stored:
                self.state = 'storing_carryon'
                # Usa su tiempo personal para guardar equipaje
                self.timer = self.store_delay
                # print(f"Agente del asiento {self.seat} guarda su equipaje de mano en el momento t={self.plane.time} segundos.")
                return
            elif cell_col < seat_col:
                next_cell = (cell_row, cell_col + 1)
            else:
                next_cell = (cell_row, cell_col - 1)

        # Si el lugar hacia el que debe avanzar esta ocupado por otro pasajero...
        if self.plane.is_cell_occupied(next_cell):
            if self.cell != None:
                cell_row, cell_col = self.cell
                next_row, next_col = next_cell

                if cell_row == next_row and next_col != cell_col:
                    adjacent_passenger = self.plane.passenger_at_seat.get(next_cell)
                    if adjacent_passenger != None and adjacent_passenger.state == 'seated':
                        adjacent_passenger.receive_get_up_request()
                else:
                    self.waiting_timer = 3
                    # Cuando retome la marcha, usará su velocidad personal
                    self.timer = self.walk_delay
            return

        if (self.waiting_timer > 0):
            self.waiting_timer -= 1
            return

        if (self.timer != 0):
            self.timer -= 1
            return

        # Actualiza su posición en la grilla
        prev_cell = self.cell
        self.cell = next_cell
        if prev_cell != None:
            self.plane.plane_grid[prev_cell] = 0
        self.plane.plane_grid[self.cell] = 1
        # print(f"Agente del asiento {self.seat} avanza a {self.cell} en el momento t={self.plane.time} segundos.")

        if self.cell == self.seat:
            self.state = 'sitting'
            # Usa su tiempo personal para sentarse
            self.timer = self.sit_delay
        else:
            # Reasignamos su velocidad de caminata personal para el próximo tramo
            self.timer = self.walk_delay

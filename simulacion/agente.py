# Para poder usar el tipo `PlaneModel` sin tener problemas con el interprete
from __future__ import annotations

# Para lidiar con probabilidades y aleatoriedad usamos este módulo
import random

# Constantes de utilidad que nos indican el rango apróximado que demora un
# pasajero en realizar cada acción (en segundos),
STORE_CARRYON_MIN = 12
STORE_CARRYON_MAX = 32

SIT_MIN = 4
SIT_MAX = 12

GET_UP_MIN = 3
GET_UP_MAX = 5

# El agente de nuestro modelo es el pasajero
class PassengerAgent:

    # Método constructor de la clase pasajero
    def __init__(self, seat: tuple[int, int], carryon: bool, plane: PlaneModel):  # type: ignore

        # Atributos de la clase pasajero

        # Indica el asiento del pasajero
        self.seat: tuple[int, int] = seat

        # Indica si el pasajero posee o no equipaje de mano
        self.carryon: bool = carryon

        # Indica si el pasajero llegó a su asiento (y terminó de sentarse)
        self.arrived_at_seat: bool = False

        # Indica si el pasajero ingreso al avión
        self.is_active = False

        # Indica la posición actual del pasajero en el avión
        self.cell: tuple[int, int] | None = None

        # Indica el avión en el que se encuentra/va ingresar el pasajero
        self.plane = plane

        # Indica el estado en el que se encuentra el pasajero.
        # Estados posibles:
        # 'walking'              -> avanza por el pasillo/la fila
        # 'storing_carryon'      -> guarda el equipaje
        # 'sitting'              -> se está sentando 
        # 'seated'               -> sentado
        # 'getting_up'           -> se está parando para dejar pasar
        # 'exchanging_positions' -> ya de pie, espera a que el otro pase

        # Flujo normal: walking -> [storing_carryon -> walking] -> sitting -> seated
        # Flujo al dejar pasar: seated -> getting_up -> exchanging_positions -> seated

        # Al ingresar al avión, te encontras caminando
        self.state: str = 'walking'

        # Indica los segundos restantes que le quedan al pasajero
        # para concretar la acción que esta llevando a cabo
        self.timer: int = 0

        # Indica si el pasajero guardo el equipaje de mano solo si es que
        # efectivamente posee equipaje de mano en primer lugar
        if carryon is True:
            self.carryon_stored: bool | None = False
        else:
            self.carryon_stored: bool | None = None

    # Método de activación del agente pasajero
    # Marca el ingreso del pasajero al avión (aún sin posición asignada en el avión)
    def activate(self):
        if self.is_active:
            return
        self.is_active = True
        print(f"Agente del asiento {self.seat} ingresa al avión en el momento t={self.plane.time} segundos.")

    # Método orquestrador
    # Determina las acciones de cada agente pasajero según el estado en qué se encuentre
    # La gracia es que con el self.timer los agentes van alternando sus estados y acciones
    # una vez concretan cada acción
    def orchestrator(self):

        # Si no el pasajero no esta activo no hay acción por orquestrar
        if not self.is_active:
            return

        # Si se encuentra caminando entonces que avance hacia su asiento
        if self.state == 'walking':
            self.walk_forward()

        # Si se encuentra guardando el equipaje de mano entonces que lo siga haciendo hasta terminar
        elif self.state == 'storing_carryon':
            self.store_carryon()

        # Si se encuentra sentandose entonces que lo siga haciendo hasta terminar
        elif self.state == 'sitting':
            self.sit_down()

        # Si se encuentra parandose entonces que lo siga haciendo hasta terminar
        elif self.state == 'getting_up':
            self.get_up()

        # Si se encuentra intercambiando posiciones con otro pasajero entonces que lo siga haciendo hasta terminar
        elif self.state == 'exchanging_positions':
            self.exchange_positions()

        # Finalmente, 'seated' no hace nada

    # Método para guardar equipaje de mano
    # Una vez lo hace sigue su camino para poder sentarse en el asiento asignado
    def store_carryon(self):
        self.timer -= 1
        if self.timer == 0:
            self.carryon_stored = True
            self.state = 'walking'

    # Método para sentarse
    # Una vez lo hace ya ha conseguido su asiento y ha concretado su objetivo
    def sit_down(self):
        self.timer -= 1
        if self.timer == 0:
            self.state = 'seated'
            self.arrived_at_seat = True
            print(f"Agente del asiento {self.seat} se sienta en el momento t={self.plane.time} segundos.")

    # Método para pedirle a un pasajero que se levante de su asiento
    # Este método no lo llama nunca un agente por su cuenta sino que el agente lo llama para el pasajero adyacente
    def receive_get_up_request(self):
        # Si el pasajero adyacente no esta sentado no se hace nada (no tiene mucho sentido)
        if self.state != 'seated':
            return
        # El pasajero adyacente comienza a levantarse
        self.state = 'getting_up'
        self.timer = random.randint(GET_UP_MIN, GET_UP_MAX)
        print(f"Agente del asiento {self.seat} se levanta para dejar pasar en el momento t={self.plane.time} segundos.")

    # Método para levantarse de su asiento
    # Viene precedido de una solicitud para que uno se levante mediada por un pasajero ajeno
    # Una vez el pasajero se levanta procede a intercambiar posiciones con el pasajero que hizo la solicitud
    def get_up(self):
        self.timer -= 1
        if self.timer == 0:
            self.plane.plane_grid[self.seat] = 0
            self.state = 'exchanging_positions'

    # Método de intercambio de posiciones para que el pasajero que se levante y aquel que quiere sentarse lo hagan
    # Ya el que se tenía que levantar está de pie. Se vuelve a sentar recién cuando la celda de su asiento queda libre 
    # (es decir, cuando el que pasaba ya siguió hacia su propio asiento). Así evitamos que los dos ocupen la misma celda
    def exchange_positions(self):
        if self.plane.plane_grid[self.seat] == 0:
            self.plane.plane_grid[self.seat] = 1
            self.state = 'seated'
            print(f"Agente del asiento {self.seat} se vuelve a sentar en el momento t={self.plane.time} segundos.")

    # Método para avanzar hacia el asiento
    def walk_forward(self):
        if self.cell is None:
            next_cell = (0, 2)
        else:
            cell_row, cell_col = self.cell
            seat_row, seat_col = self.seat
            if cell_row < seat_row:
                next_cell = (cell_row + 1, cell_col)
            elif cell_col == 2 and self.carryon and not self.carryon_stored:
                # Llega al pasillo de la fila, antes de ir al asiento guarda
                # el equipaje, y luego se sienta o espera que lo dejen pasar
                self.state = 'storing_carryon'
                self.timer = random.randint(STORE_CARRYON_MIN, STORE_CARRYON_MAX)
                print(f"Agente del asiento {self.seat} guarda su equipaje de mano en el momento t={self.plane.time} segundos.")
                return
            elif cell_col < seat_col:
                next_cell = (cell_row, cell_col + 1)
            else:
                next_cell = (cell_row, cell_col - 1)

        if self.plane.is_cell_occupied(next_cell):
            if self.cell is not None:
                cell_row, cell_col = self.cell
                next_row, next_col = next_cell
                if cell_row == next_row and next_col != cell_col:
                    # Nos bloquea alguien en la misma fila (no en el
                    # pasillo): si ya está sentado, le pedimos que se pare
                    adjacent_passenger = self.plane.passenger_at_seat.get(next_cell)
                    if adjacent_passenger is not None and adjacent_passenger.state == 'seated':
                        adjacent_passenger.receive_get_up_request()
                # Si no, es alguien delante en el pasillo: no se hace nada
                # más que esperar a que se mueva. En ambos casos,
                # se queda esperando sin hacer nada un turno.
            return

        # Solo liberamos la celda anterior si existía (self.cell != None)
        prev_cell = self.cell
        self.cell = next_cell
        if prev_cell is not None:
            self.plane.plane_grid[prev_cell] = 0
        self.plane.plane_grid[self.cell] = 1
        print(f"Agente del asiento {self.seat} avanza a {self.cell} en el momento t={self.plane.time} segundos.")
        if self.cell == self.seat:
            # Llegó a su asiento: ahora tarda un rato en sentarse
            self.state = 'sitting'
            self.timer = random.randint(SIT_MIN, SIT_MAX)
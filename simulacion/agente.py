import random

# Constantes de utilidad respecto a los intervalos de tiempo
# en segundos según la acción de cada pasajero

STORE_CARRYON_MIN = 12
STORE_CARRYON_MAX = 32
 
SIT_MIN = 4
SIT_MAX = 12
 
GET_UP_MIN = 3
GET_UP_MAX = 5

class PassengerAgent:
    def __init__(self, seat: tuple[int, int], carryon: bool, plane: Plane):  # type: ignore
        self.seat: tuple[int, int] = seat
        self.carryon: bool = carryon
        self.arrived_at_seat: bool = False
        self.is_active = False
        self.cell: tuple[int, int] | None = None
        self.plane = plane
 
        # Estados: 'walking', 'storing_carryon', 'sitting',
        # 'exchanging_positions' (mientras deja pasar a alguien),
        # 'seated' (terminal, después de haber dejado pasar a alguien)
        self.state: str = 'walking'
        self.timer: int = 0  # segundos restantes por cada acción
        if carryon is True:
            self.carryon_stored: bool | None = False
        else:
            self.carryon_stored: bool | None = None
 
        # Hacía falta una segunda variable para la acción de
        # 'exchanging_positions', porque tiene la fase del
        # tiempo que tarda en pararse (self.timer cuenta eso), y después
        # queda de pie, esperando a que el que pasa termine de pasar.
        # self.standing distingue cuál de las dos fases es la que se 
        # encuentra en ese momento
        self.standing: bool = False

    
    def activate(self):
        if self.is_active:
            return
        self.is_active = True
        print(f"Agente del asiento {self.seat} ingresa al avión en el momento t={self.plane.time} segundos.")

    # Determina las acciones de cada agente pasajero según el estado en qué se encuentre
    def orchestrator(self):
        if not self.is_active:
            return
        if self.state == 'exchanging_positions':
            self.exchange_positions()
            return
        if self.arrived_at_seat:
            return
        if self.state == 'storing_carryon':
            self.store_carryon()
        elif self.state == 'sitting':
            self.sit_down()
        else:
            self.walk_forward()
 
    def store_carryon(self):
        self.timer -= 1
        if self.timer == 0:
            self.carryon_stored = True
            self.state = 'walking'
 
    def sit_down(self):
        self.timer -= 1
        if self.timer == 0:
            self.arrived_at_seat = True
            print(f"Agente del asiento {self.seat} se sienta en el momento t={self.plane.time} segundos.")
 
    def get_up(self):
        if self.state == 'exchanging_positions':
            return
        self.state = 'exchanging_positions'
        self.standing = False
        self.timer = random.randint(GET_UP_MIN, GET_UP_MAX)
        print(f"Agente del asiento {self.seat} se levanta para dejar pasar en el momento t={self.plane.time} segundos.")
 
    def exchange_positions(self):
        # Se está parando (dura self.timer segundos)
        if not self.standing:
            self.timer -= 1
            if self.timer <= 0:
                self.standing = True
                # Recién al terminar de pararse, se libera la celda
                self.plane.plane_grid[self.seat] = 0
            return
 
        # Ya está de pie. Se vuelve a sentar recién cuando la celda
        # de su asiento queda libre de (es decir, cuando el pasajero que
        # pasaba ya se movió a su propio asiento). Así evitamos que los dos
        # se traben tratando de ocupar la misma cell al mismo tiempo.
        if self.plane.plane_grid[self.seat] == 0:
            self.plane.plane_grid[self.seat] = 1
            self.state = 'seated'
            print(f"Agente del asiento {self.seat} se vuelve a sentar en el momento t={self.plane.time} segundos.")
 
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
            elif cell_col > seat_col:
                next_cell = (cell_row, cell_col - 1)
            else:
                self.state = 'sitting'
                self.timer = random.randint(SIT_MIN, SIT_MAX)
                return
 
        if self.plane.is_cell_occupied(next_cell):
            if self.cell is not None:
                cell_row, cell_col = self.cell
                next_row, next_col = next_cell
                if cell_row == next_row and next_col != cell_col:
                    # Nos bloquea alguien en la misma fila (no en el
                    # pasillo) si ya está sentado, le pedimos que se pare
                    adjacent_passenger = self.plane.passenger_at_seat.get(next_cell)
                    if adjacent_passenger is not None and adjacent_passenger.arrived_at_seat and adjacent_passenger.state != 'exchanging_positions':
                        adjacent_passenger.get_up()
                # Si no, es alguien delante en el pasillo no se hace nada
                # más que esperar a que se mueva. En ambos casos,
                # se queda esperando sin hacer nada un turno.
            return
 
        # Ahora solo liberamos la celda anterior si existía (self.cell != None)
        prev_cell = self.cell
        self.cell = next_cell 
        if prev_cell is not None:
            self.plane.plane_grid[prev_cell] = 0
        self.plane.plane_grid[self.cell] = 1
        print(f"Agente del asiento {self.seat} avanza a {self.cell} en el momento t={self.plane.time} segundos.")
        if self.cell == self.seat:
            self.arrived_at_seat = True
 

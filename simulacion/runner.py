# Para crear la carpeta de resultados y armar la ruta del archivo
import os

# Para ponerle al archivo de resultados la fecha y hora en que se generó
from datetime import datetime

# Para poder silenciar los prints de los agentes cuando no queremos verlos
import io
import contextlib

# Importamos el ambiente de nuestro modelo, el avión
from ambiente_fisico import PlaneModel

# Importamos las funciones de visualización
from animacion import animar_embarque

# Políticas de embarque que simulamos por defecto
METHODS = ['rand', 'btf', 'wilma', 'stfn']

# Límite de segundos simulados, para que una simulación que se trabe no
# corra para siempre. Con 100 pasajeros la política más lenta (btf) ronda
# los 1100 segundos, así que 2000 deja margen de sobra
MAX_STEPS = 2000

# Método para correr una única simulación
# Devuelve el tiempo total de embarque (en segundos)
# Si verbose es True, se muestran las acciones de cada pasajero paso a paso
# y el tiempo final; si es False, la simulación corre en silencio
def run_single(n_passengers: int, p_carryon: float, method: str, verbose: bool = False) -> int:

    # Creamos el avión con sus pasajeros según la política elegida
    model = PlaneModel(n=n_passengers, p=p_carryon, onboarding_method=method)

    # Si no queremos ver los prints de los agentes, redirigimos la salida
    # a un buffer que después se descarta
    if verbose:
        salida = contextlib.nullcontext()
    else:
        salida = contextlib.redirect_stdout(io.StringIO())

    # Avanzamos la simulación segundo a segundo hasta que todos estén
    # sentados o se alcance el límite de pasos
    with salida:
        while not model.all_passengers_seated() and model.time < MAX_STEPS:
            model.step()

    # Esta advertencia se muestra siempre, aunque verbose sea False, porque
    # indica que el resultado de esta simulación no es válido
    if not model.all_passengers_seated():
        print(f"Advertencia sobre {method}: no todos se sentaron en {MAX_STEPS} pasos.")

    if verbose:
        print(f"{method}: embarque completo en {model.time}s")

    return model.time

# Método para visualizar una simulación de un tipo de embarque
def run_and_show(
    n_passengers: int = 100,
    p_carryon: float = 0.5,
    method:str = 'rand',
) -> str:
    """
    Corre una simulación con la política seleccionada y guarda un GIF con su visualización.

    Parámetros:
        n_passengers:  cantidad de pasajeros.
        p_carryon:     probabilidad de que un pasajero tenga carry-on.
        method:       política a simular.

    """
    # Creamos el avión con sus pasajeros según la política elegida
    model = PlaneModel(n=n_passengers, p=p_carryon, onboarding_method=method)

    # Redirigimos la salida a un buffer que después se descarta
    salida = contextlib.redirect_stdout(io.StringIO())

    # Creamos un archivo de texto en el cual guardamos el plane_grid para cada momento en el tiempo
    output_dir: str = '../resultados'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(output_dir, f'simulaciones/sim_record_{timestamp}.txt')
    sr = open(file=filename, mode='x')

    # Avanzamos la simulación segundo a segundo hasta que todos estén
    # sentados o se alcance el límite de pasos
    with salida:
        while not model.all_passengers_seated() and model.time < MAX_STEPS:
            model.step()
            sr.write(str(model.plane_grid))


    # Esta advertencia se muestra siempre, aunque verbose sea False, porque
    # indica que el resultado de esta simulación no es válido
    if not model.all_passengers_seated():
        print(f"Advertencia sobre {method}: no todos se sentaron en {MAX_STEPS} pasos.")

    sr.close()

    ruta_gif = animar_embarque(
        ruta_txt=filename,
        nombre_salida=f"{method}.gif",   # p.ej. "steffen.gif", "back_to_front.gif"
        titulo=f"Política: {method}",
    )
    return ruta_gif

# Método para correr n simulaciones por cada política de embarque
def run_simulations(
    n_simulations: int = 30,
    n_passengers: int = 100,
    p_carryon: float = 0.5,
    methods: list[str] | None = None,
    verbose: bool = False,
) -> dict[str, list[int]]:
    """
    Corre n_simulations por cada política de embarque.

    Parámetros:
        n_simulations: cantidad de simulaciones por política.
        n_passengers:  cantidad de pasajeros por simulación.
        p_carryon:     probabilidad de que un pasajero tenga carry-on.
        methods:       lista de políticas a simular (por defecto las 4).
        verbose:       si True, imprime el resultado de cada simulación.

    Retorna: diccionario con la política como clave y la lista de demoras totales por simulación.

    Ejemplo de retorno:
        {
            'rand':  [430, 512, 487, ...],
            'btf':   [846, 903, 821, ...],
            'wilma': [352, 389, 371, ...],
            'stfn':  [249, 261, 244, ...],
        }
    """

    # Si no se indican políticas, simulamos las cuatro
    if methods is None:
        methods = METHODS

    # Armamos un diccionario con una lista vacía por cada política
    results: dict[str, list[int]] = {m: [] for m in methods}  # dict comprehension

    for method in methods:
        for i in range(n_simulations):
            # Cada simulación individual corre siempre en silencio: con
            # verbose acá solo mostramos el resumen de cada una, no las
            # miles de acciones de los pasajeros
            time = run_single(n_passengers, p_carryon, method, verbose=False)
            results[method].append(time)

            if verbose:
                print(f"{method} simulación {i+1}/{n_simulations}: {time}s")

    return results

# Método para guardar los resultados de run_simulations() en un archivo .txt
# Incluye los tiempos individuales y el promedio, mínimo y máximo por política
# Devuelve la ruta del archivo generado
def save_results(
    results: dict[str, list[int]],
    n_passengers: int,
    p_carryon: float,
    output_dir: str = '../resultados',
) -> str:

    # Creamos la carpeta de resultados si todavía no existe
    os.makedirs(output_dir, exist_ok=True)

    # Le ponemos al archivo la fecha y hora para no pisar resultados anteriores
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(output_dir, f'resultados_{timestamp}.txt')

    # Todas las políticas tienen la misma cantidad de simulaciones, así que
    # la tomamos de la primera
    n_simulations = len(next(iter(results.values())))

    with open(filename, 'w') as f:

        # Encabezado con los parámetros de la simulación
        f.write(f"Resultados de simulación — {timestamp}\n")
        f.write(f"Pasajeros: {n_passengers} | P(carry-on): {p_carryon} | Simulaciones por política: {n_simulations}\n")
        f.write("=" * 60 + "\n\n")

        # Un bloque por política con sus estadísticas y todos sus tiempos
        for method, times in results.items():
            avg = sum(times) / len(times)
            f.write(f"[{method}]\n")
            f.write(f"  Promedio : {avg:.1f}s\n")
            f.write(f"  Mínimo   : {min(times)}s\n")
            f.write(f"  Máximo   : {max(times)}s\n")
            f.write(f"  Tiempos  : {times}\n\n")

    print(f"Resultados guardados en {filename}")
    return filename
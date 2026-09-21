import os
from datetime import datetime
from ambiente_fisico import PlaneModel

METHODS = ['rand', 'btf', 'wilma', 'stfn']
MAX_STEPS = 2000  # límite de turnos (no sé cuál es la cota del peor caso)

# Correr una simulación
def run_single(n_passengers: int, p_carryon: float, method: str) -> int:
    """Corre una única simulación y devuelve el tiempo total de embarque (en segundos)."""
    model = PlaneModel(n=n_passengers, p=p_carryon, onboarding_method=method)

    while not model.all_passengers_seated() and model.time < MAX_STEPS:
        model.step()

    if not model.all_passengers_seated():
        print(f"Adevertencia sobre {method}: no todos se sentaron en {MAX_STEPS} pasos.")
        
    print(f"{method}: embarque completo en {model.time}s")
    return model.time

# Correr n simulaciones
def run_simulations(
    n_simulations: int = 30,
    n_passengers: int = 100,
    p_carryon: float = 0.5,
    methods: list[str] | None = None,
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
    if methods is None:
        methods = METHODS

    results: dict[str, list[int]] = {m: [] for m in methods} # dict comprehension

    for method in methods:
        for i in range(n_simulations):
            time = run_single(n_passengers, p_carryon, method)
            results[method].append(time)

            print(f"{method} simulación {i+1}/{n_simulations}: {time}s")
    return results

def save_results(
    results: dict[str, list[int]],
    n_passengers: int,
    p_carryon: float,
    output_dir: str = '../resultados',
) -> str:
    """
    Guarda los resultados de run_simulations() en un archivo .txt en output_dir.
    Incluye los tiempos individuales y el promedio por método.
    Devuelve el path del archivo generado.
    """
    os.makedirs(output_dir, exist_ok=True)
 
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(output_dir, f'resultados_{timestamp}.txt')
 
    n_simulations = len(next(iter(results.values())))
 
    with open(filename, 'w') as f:
        f.write(f"Resultados de simulación — {timestamp}\n")
        f.write(f"Pasajeros: {n_passengers} | P(carry-on): {p_carryon} | Simulaciones por política: {n_simulations}\n")
        f.write("=" * 60 + "\n\n")
 
        for method, times in results.items():
            avg = sum(times) / len(times)
            f.write(f"[{method}]\n")
            f.write(f"  Promedio : {avg:.1f}s\n")
            f.write(f"  Mínimo   : {min(times)}s\n")
            f.write(f"  Máximo   : {max(times)}s\n")
            f.write(f"  Tiempos  : {times}\n\n")
 
    print(f"Resultados guardados en {filename}")
    return filename

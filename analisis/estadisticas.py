# Para ubicar la raíz del repositorio sin depender del directorio de trabajo
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
 
# Módulo con todas las rutas del proyecto (también deja simulacion/ y
# analisis/ en el path, así el import de abajo funciona siempre)
import rutas


from runner import run_simulations, save_results

datos:list = list()

for i in range(11):
    datos.append(run_simulations(n_simulations=10000, n_passengers=100, p_carryon=(i/10)))
    save_results(results = datos[i], n_passengers=100, p_carryon=(i/10), output_dir=rutas.RESULTADOS) # type: ignore


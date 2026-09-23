# Versión de estadisticas.py para el agente bonus (velocidades heterogéneas).
# Corre el mismo barrido sobre la probabilidad de carry-on, pero poblando el
# avión con el PassengerAgent de bonus_agente.py, y guarda los resultados en
# una carpeta aparte para no mezclarlos con los del modelo base.

# Para ubicar la raíz del repositorio sin depender del directorio de trabajo
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Módulo con todas las rutas del proyecto (también deja simulacion/ y
# analisis/ en el path, así los imports de abajo funcionan siempre)
import rutas

from runner import run_simulations, save_results
from bonus_agente import BonusPassengerAgent as BonusAgent

# Carpeta propia para los resultados del bonus. Se lee después con
# leer_carpeta(rutas.RESULTADOS / 'grandes_simulaciones_bonus')
CARPETA_BONUS = rutas.RESULTADOS / 'grandes_simulaciones_bonus'

P_CARRYON = 0.8

datos = run_simulations(n_simulations=5000, n_passengers=100, p_carryon=P_CARRYON, agent_class=BonusAgent)  # type: ignore
save_results(results=datos, n_passengers=100, p_carryon=P_CARRYON, output_dir=CARPETA_BONUS, etiqueta='bonus')  # type: ignore
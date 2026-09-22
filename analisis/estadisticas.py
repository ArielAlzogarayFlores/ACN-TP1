import numpy as np

import sys
sys.path.insert(0, "/home/josedesgtt/Documentos/Trabajos de la facu/Cursada tercer año/Segundo semestre/acn/ACN-TP1/simulacion")
from runner import run_simulations, save_results

# Revisar

datos:list = list()

for i in range(11):
    datos.append(run_simulations(n_simulations=5000, n_passengers=100, p_carryon=(i/10)))
    save_results(results = datos[i], n_passengers=100, p_carryon=(i/10), output_dir='resultados')


# Módulo central de rutas del proyecto.
#
# El problema que resuelve: si escribimos rutas relativas como '../resultados'
# o 'resultados', lo que pase depende de DESDE DÓNDE se ejecuta el programa
# (el "directorio de trabajo"), no de dónde está el archivo .py. Por eso a uno
# le anda y a otro no, según si corre el notebook, un script desde la raíz del
# repo o desde la carpeta simulacion.
#
# La solución es calcular todo a partir de la ubicación de ESTE archivo, que
# siempre está en la raíz del repositorio, usando __file__.

import sys
from pathlib import Path

# Carpeta raíz del repositorio (donde está este archivo)
RAIZ = Path(__file__).resolve().parent

# Carpetas de código
SIMULACION = RAIZ / 'simulacion'
ANALISIS = RAIZ / 'analisis'
NOTEBOOKS = RAIZ / 'notebooks'

# Carpetas de salida
RESULTADOS = RAIZ / 'resultados'
SIMULACIONES = RESULTADOS / 'simulaciones'
VISUALIZACIONES = RESULTADOS / 'visualizaciones'

# Agregamos las carpetas de código al path de Python, así cualquier archivo
# puede hacer `from ambiente_fisico import PlaneModel` o `from animacion
# import animar_embarque` sin importar desde dónde se lo ejecute
for carpeta in (SIMULACION, ANALISIS):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))


# Método para crear las carpetas de salida si todavía no existen
# (las llamamos antes de escribir cualquier archivo de resultados)
def preparar_carpetas():
    for carpeta in (RESULTADOS, SIMULACIONES, VISUALIZACIONES):
        carpeta.mkdir(parents=True, exist_ok=True)


# Método para encontrar la raíz del repo desde un notebook.
# Los notebooks no tienen __file__, así que subimos carpeta por carpeta desde
# el directorio actual hasta encontrar este mismo archivo (rutas.py)
def buscar_raiz(desde=None):
    actual = Path(desde) if desde is not None else Path.cwd()
    actual = actual.resolve()
    for carpeta in (actual, *actual.parents):
        if (carpeta / 'rutas.py').exists():
            return carpeta
    raise FileNotFoundError(
        "No se encontró rutas.py: ¿el notebook está dentro del repositorio ACN-TP1?"
    )
# Lector de los archivos de resultados que genera save_results() en runner.py.
#
# Un archivo tiene este formato:
#
#     Resultados de simulación — 20260922_175057
#     Pasajeros: 100 | P(carry-on): 0.0 | Simulaciones por política: 5000
#     ============================================================
#
#     [rand]
#       Promedio : 394.2s
#       Desvío   : 45.8s
#       IC 95%   : [393.0s, 395.5s]
#       Mínimo   : 220s
#       Máximo   : 565s
#       Tiempos  : [378, 431, 355, ...]
#
#     [btf]
#       ...
#
# Lo que nos interesa de verdad son los tiempos crudos, porque a partir de
# ellos podemos recalcular cualquier estadístico, hacer histogramas o ajustar
# distribuciones. Las estadísticas del encabezado las guardamos igual, para
# poder chequear que lo que leímos coincide con lo que se escribió.

# Para ubicar la raíz del repositorio sin depender del directorio de trabajo
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Módulo con todas las rutas del proyecto
import rutas

import re
import ast
from dataclasses import dataclass, field

import numpy as np


# Expresión regular del encabezado: de ahí sacamos los parámetros de la corrida
_RE_ENCABEZADO = re.compile(
    r"Pasajeros:\s*(\d+)\s*\|\s*P\(carry-on\):\s*([\d.]+)\s*\|\s*"
    r"Simulaciones por política:\s*(\d+)"
)

# Una línea de estadística: "  Promedio : 394.2s"
_RE_CAMPO = re.compile(r"^\s{2,}(\S[^:]*?)\s*:\s*(.+)$")

# El nombre de una política entre corchetes: "[rand]"
_RE_POLITICA = re.compile(r"^\[([^\]]+)\]\s*$")

# Un intervalo: "[393.0s, 395.5s]"
_RE_INTERVALO = re.compile(r"^\[\s*([\d.]+)s\s*,\s*([\d.]+)s\s*\]$")


@dataclass
class ResultadoPolitica:
    """Los datos de una política dentro de un archivo."""

    metodo: str

    # Los 5000 tiempos de embarque, como array de numpy para poder hacer
    # tiempos.mean(), np.histogram(tiempos), etc. sin convertir nada
    tiempos: np.ndarray

    # Las estadísticas tal como estaban escritas en el archivo. Son un control,
    # no la fuente de verdad: si querés el promedio, usá tiempos.mean()
    estadisticas: dict = field(default_factory=dict)

    def __len__(self):
        return len(self.tiempos)


@dataclass
class ResultadoSimulacion:
    """Todo el contenido de un archivo de resultados."""

    archivo: Path
    timestamp: str
    n_passengers: int
    p_carryon: float
    n_simulations: int

    # metodo -> ResultadoPolitica
    politicas: dict

    def tiempos(self, metodo: str) -> np.ndarray:
        """Atajo para los tiempos crudos de una política."""
        return self.politicas[metodo].tiempos

    @property
    def metodos(self) -> list:
        return list(self.politicas.keys())


def leer_resultados(nombre_archivo) -> ResultadoSimulacion:
    """
    Lee un archivo de resultados y devuelve un ResultadoSimulacion.

    El parámetro puede ser el nombre del archivo (se busca en resultados/) o
    una ruta completa.
    """
    ruta = Path(nombre_archivo)
    if not ruta.is_absolute() and not ruta.exists():
        ruta = rutas.RESULTADOS / ruta
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo de resultados: {ruta}")

    texto = ruta.read_text(encoding="utf-8")
    lineas = texto.splitlines()

    # --- Encabezado ---
    encabezado = _RE_ENCABEZADO.search(texto)
    if encabezado is None:
        raise ValueError(
            f"'{ruta.name}' no parece un archivo de resultados: no tiene el "
            "encabezado con los pasajeros y la probabilidad de carry-on."
        )
    n_passengers = int(encabezado.group(1))
    p_carryon = float(encabezado.group(2))
    n_simulations = int(encabezado.group(3))

    # El timestamp está en la primera línea, después del guión largo
    timestamp = lineas[0].split("—")[-1].strip() if lineas else ""

    # --- Bloques por política ---
    politicas = dict()
    metodo_actual = None
    tiempos_actual = None
    estadisticas_actual = dict()

    def cerrar_bloque():
        """Guarda el bloque que veníamos leyendo, si había alguno."""
        if metodo_actual is None:
            return
        if tiempos_actual is None:
            raise ValueError(
                f"La política '{metodo_actual}' en '{ruta.name}' no tiene "
                "la línea de Tiempos."
            )
        politicas[metodo_actual] = ResultadoPolitica(
            metodo=metodo_actual,
            tiempos=tiempos_actual,
            estadisticas=dict(estadisticas_actual),
        )

    for linea in lineas:
        politica = _RE_POLITICA.match(linea)
        if politica is not None:
            cerrar_bloque()
            metodo_actual = politica.group(1)
            tiempos_actual = None
            estadisticas_actual = dict()
            continue

        campo = _RE_CAMPO.match(linea)
        if campo is None or metodo_actual is None:
            continue

        clave, valor = campo.group(1).strip(), campo.group(2).strip()

        # La lista de tiempos es el dato principal
        if clave.lower().startswith("tiempos"):
            tiempos_actual = np.array(ast.literal_eval(valor), dtype=int)
        else:
            estadisticas_actual[clave] = _convertir(valor)

    cerrar_bloque()

    if not politicas:
        raise ValueError(f"'{ruta.name}' no contiene ninguna política.")

    # Control de consistencia: la cantidad de tiempos tiene que coincidir con
    # lo que dice el encabezado
    for metodo, datos in politicas.items():
        if len(datos) != n_simulations:
            print(f"Aviso: en '{ruta.name}' la política {metodo} tiene "
                  f"{len(datos)} tiempos pero el encabezado dice {n_simulations}.")

    return ResultadoSimulacion(
        archivo=ruta,
        timestamp=timestamp,
        n_passengers=n_passengers,
        p_carryon=p_carryon,
        n_simulations=n_simulations,
        politicas=politicas,
    )


def _convertir(valor: str):
    """Convierte el valor de una estadística al tipo que corresponda."""
    intervalo = _RE_INTERVALO.match(valor)
    if intervalo is not None:
        return (float(intervalo.group(1)), float(intervalo.group(2)))
    try:
        return float(valor.rstrip("s"))
    except ValueError:
        return valor


# ============================================================
# Varios archivos: el barrido sobre la probabilidad de carry-on
# ============================================================

@dataclass
class Barrido:
    """
    Una colección de resultados ordenada por probabilidad de carry-on, que es
    como los generamos en estadisticas.py (un archivo por cada valor de p).
    """

    resultados: list

    @property
    def valores_p(self) -> np.ndarray:
        return np.array([r.p_carryon for r in self.resultados])

    @property
    def metodos(self) -> list:
        return self.resultados[0].metodos if self.resultados else []

    def tiempos(self, metodo: str) -> np.ndarray:
        """
        Matriz de tiempos de una política: una fila por valor de p y una
        columna por simulación. Sirve para histogramas por valor de p.
        """
        return np.array([r.tiempos(metodo) for r in self.resultados])

    def promedios(self, metodo: str) -> np.ndarray:
        """Promedio de una política para cada valor de p (para plotear)."""
        return np.array([r.tiempos(metodo).mean() for r in self.resultados])

    def desvios(self, metodo: str) -> np.ndarray:
        """Desvío muestral de una política para cada valor de p."""
        return np.array([r.tiempos(metodo).std(ddof=1) for r in self.resultados])

    def errores_estandar(self, metodo: str) -> np.ndarray:
        """Error estándar del promedio, para las barras de error del gráfico."""
        return np.array([r.tiempos(metodo).std(ddof=1) / np.sqrt(len(r.tiempos(metodo)))
                         for r in self.resultados])

    def faltantes(self, paso: float = 0.1) -> list:
        """
        Qué valores de p entre 0 y 1 todavía no fueron simulados. Útil mientras
        el barrido está a medio correr.
        """
        esperados = np.round(np.arange(0, 1 + paso / 2, paso), 10)
        presentes = np.round(self.valores_p, 10)
        return [float(p) for p in esperados if p not in presentes]


def leer_carpeta(carpeta=None, patron: str = "resultados_*.txt",
                 avisar_faltantes: bool = True) -> Barrido:
    """
    Lee todos los archivos de resultados de una carpeta y los ordena por
    probabilidad de carry-on. Por defecto usa la carpeta resultados/ del repo.

    Si hay dos archivos con el mismo p (por ejemplo, porque repitieron una
    corrida), se queda con el más nuevo según el nombre del archivo.
    """
    carpeta = Path(carpeta) if carpeta is not None else rutas.RESULTADOS
    archivos = sorted(carpeta.glob(patron))
    if not archivos:
        raise FileNotFoundError(f"No hay archivos que coincidan con '{patron}' en {carpeta}")

    por_p = dict()
    for archivo in archivos:
        resultado = leer_resultados(archivo)
        por_p[resultado.p_carryon] = resultado  # el último gana

    resultados = [por_p[p] for p in sorted(por_p)]
    barrido = Barrido(resultados=resultados)

    if avisar_faltantes:
        faltan = barrido.faltantes()
        if faltan:
            print("Aviso: todavía faltan los valores de p:",
                  ", ".join(f"{p:.1f}" for p in faltan))

    return barrido
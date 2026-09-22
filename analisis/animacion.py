"""
analisis/animacion.py

Genera una animación (GIF) del embarque del avión a partir del archivo .txt
que graba `ambiente_fisico.py` con todos los estados de la grilla.

Uso típico desde runner.py / el notebook:

    from analisis.animacion import animar_embarque

    ruta_gif = animar_embarque(
        "resultados/simulation_record.txt",
        titulo="Política: Steffen",
    )

Guarda el GIF en resultados/visualizaciones/ (la crea si no existe) y
devuelve la ruta del archivo generado.
"""

import os
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter

# ---------- Rutas de assets propios de este módulo (funcionan sea cual sea el cwd) ----------
_DIR_MODULO = Path(__file__).resolve().parent
FUSELAJE_VECTOR_DEFAULT = str(_DIR_MODULO / "assets" / "avion_vector.png")

# Rutas del proyecto (calculadas desde la raíz del repo, no desde el cwd)
import sys
sys.path.append(str(_DIR_MODULO.parent))
import rutas

# ---------- Paleta de colores ----------
COLOR_LIBRE = "#E8F5E9"
COLOR_BORDE_LIBRE = "#81C784"
COLOR_OCUPADO = "#64B5F6"
COLOR_BORDE_OCUPADO = "#1976D2"
COLOR_NUEVO = "#FFB74D"
COLOR_BORDE_NUEVO = "#E65100"
COLOR_PASILLO = "#F5F5F5"
COLOR_FUSELAJE = "#37474F"
COLOR_CAMINANDO = "#AB47BC"
COLOR_BORDE_CAMINANDO = "#6A1B9A"


# ============================================================
# 1. Parseo del .txt -> lista de matrices numpy
# ============================================================

def parsear_historial(ruta_txt):
    """
    Lee un .txt como el que genera la simulación (matrices impresas con el
    formato por defecto de numpy, pegadas una tras otra sin separador) y
    devuelve una lista de arrays numpy, uno por cada estado de la grilla.
    """
    with open(ruta_txt, "r") as f:
        contenido = f.read()

    bloques = re.findall(r"\[\[.*?\]\]", contenido, re.S)
    if not bloques:
        raise ValueError(
            f"No se encontró ninguna matriz en '{ruta_txt}'. "
            "¿Es un archivo generado por la simulación?"
        )

    historial = []
    for bloque in bloques:
        filas_n = bloque.count("\n") + 1
        numeros = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+", bloque)]
        cols_n = len(numeros) // filas_n
        historial.append(np.array(numeros).reshape(filas_n, cols_n))

    return historial


# ============================================================
# 2. Dibujo de un cuadro
# ============================================================

COLOR_MAP_ASIENTO = {
    "libre": (COLOR_LIBRE, COLOR_BORDE_LIBRE),
    "ocupado": (COLOR_OCUPADO, COLOR_BORDE_OCUPADO),
    "nuevo": (COLOR_NUEVO, COLOR_BORDE_NUEVO),
}


def _crear_asiento(ax, x, y, escala=1.0):
    """Crea (una sola vez) los dibujos de un asiento: el cuadrado, y la cabeza
    y el cuerpo del pasajero, que arrancan ocultos. Devuelve los tres para
    poder cambiarles el color o la visibilidad cuadro a cuadro, sin tener que
    volver a crearlos."""
    tam = 0.8 * escala

    # Rectangle (esquinas rectas) en vez de FancyBboxPatch: visualmente casi
    # igual de claro, pero mucho más rápido de dibujar (importa al animar
    # cientos de asientos en cientos de cuadros).
    rect = patches.Rectangle(
        (x - tam / 2, y - tam / 2), tam, tam,
        linewidth=1.8, edgecolor=COLOR_BORDE_LIBRE, facecolor=COLOR_LIBRE, zorder=2,
    )
    cabeza = patches.Circle((x, y + 0.16 * escala), 0.13 * escala,
                             facecolor="#4E342E", zorder=3, visible=False)
    cuerpo = patches.Rectangle(
        (x - 0.18 * escala, y - 0.28 * escala), 0.36 * escala, 0.3 * escala,
        facecolor=COLOR_BORDE_OCUPADO, edgecolor="none", zorder=3, visible=False,
    )
    for artista in (rect, cabeza, cuerpo):
        ax.add_patch(artista)
    return rect, cabeza, cuerpo


def _pintar_asiento(artistas, estado):
    """Actualiza un asiento ya creado según su estado."""
    rect, cabeza, cuerpo = artistas
    face, edge = COLOR_MAP_ASIENTO[estado]
    rect.set_facecolor(face)
    rect.set_edgecolor(edge)
    ocupado = estado in ("ocupado", "nuevo")
    cabeza.set_visible(ocupado)
    cuerpo.set_visible(ocupado)
    cuerpo.set_facecolor(edge)


def _dibujar_asiento(ax, x, y, estado, escala=1.0):
    """Versión de un solo uso: crea el asiento y le aplica el estado."""
    _pintar_asiento(_crear_asiento(ax, x, y, escala), estado)


def _crear_persona_pasillo(ax, x, y, escala=1.0):
    """Crea (oculto) el pasajero que camina por el pasillo de una fila."""
    halo = patches.Circle((x, y), 0.34 * escala, facecolor=COLOR_CAMINANDO,
                           edgecolor=COLOR_BORDE_CAMINANDO, linewidth=1.5,
                           alpha=0.35, zorder=3, visible=False)
    cabeza = patches.Circle((x, y + 0.14 * escala), 0.12 * escala,
                             facecolor="#4E342E", zorder=4, visible=False)
    cuerpo = patches.Rectangle(
        (x - 0.15 * escala, y - 0.24 * escala), 0.3 * escala, 0.28 * escala,
        facecolor=COLOR_BORDE_CAMINANDO, edgecolor="none", zorder=4, visible=False,
    )
    for artista in (halo, cabeza, cuerpo):
        ax.add_patch(artista)
    return halo, cabeza, cuerpo


def _dibujar_persona_pasillo(ax, x, y, escala=1.0):
    """Versión de un solo uso: crea el pasajero y lo hace visible."""
    for artista in _crear_persona_pasillo(ax, x, y, escala):
        artista.set_visible(True)


def _estado_de_asiento(fila, col, matriz_actual, matriz_anterior):
    if matriz_actual[fila, col] == 0:
        return "libre"
    if matriz_anterior is None or matriz_anterior[fila, col] == 0:
        return "nuevo"
    return "ocupado"


def _dibujar_avion_esquematico(ax, filas, cols, escala=1.0):
    """Fallback: rectángulo redondeado con nariz/cola triangulares, por si no
    se quiere usar la silueta vectorial."""
    ancho_util = (cols - 1) * escala
    alto_total = filas * escala
    margen = 0.6 * escala

    ax.add_patch(patches.FancyBboxPatch(
        (-margen, -alto_total - 0.1 * escala),
        ancho_util + 2 * margen, alto_total + 0.7 * escala,
        boxstyle="round,pad=0,rounding_size=0.35",
        linewidth=2.5, edgecolor=COLOR_FUSELAJE, facecolor="white", zorder=0,
    ))
    cx = ancho_util / 2
    ax.add_patch(patches.Polygon(
        [(-margen, 0.3 * escala), (ancho_util + margen, 0.3 * escala), (cx, 1.3 * escala)],
        closed=True, facecolor=COLOR_FUSELAJE, zorder=0,
    ))
    ax.add_patch(patches.Rectangle(
        (cx - 0.35 * escala, -alto_total - 1.1 * escala), 0.7 * escala, 0.8 * escala,
        facecolor=COLOR_FUSELAJE, zorder=0,
    ))
    ax.add_patch(patches.Rectangle(
        (cx - 0.5 * escala, -alto_total - 0.1 * escala), escala, alto_total + 0.2 * escala,
        facecolor=COLOR_PASILLO, zorder=0.5,
    ))


@lru_cache(maxsize=4)
def _leer_fuselaje(ruta_imagen):
    """Lee el PNG del fuselaje UNA sola vez y lo deja cacheado: antes se leía
    de disco en cada cuadro de la animación, que eran cientos de lecturas."""
    import matplotlib.image as mpimg
    return mpimg.imread(ruta_imagen)


def _calcular_extent_vector(filas, cols, escala, ruta_imagen):
    """Calcula el extent (left, right, bottom, top) para envolver la grilla
    con la silueta vectorial, sin dibujar nada todavía."""
    img = _leer_fuselaje(ruta_imagen)
    H, W = img.shape[0], img.shape[1]

    # Medido como FRACCIÓN del ancho/alto total de la imagen (no en píxeles
    # absolutos), para que siga funcionando bien sin importar la resolución
    # real del archivo (por ejemplo, si se reemplaza por una versión más
    # liviana). Corresponde a la zona del fuselaje con ancho constante,
    # entre las alas y el cono de cola.
    TUBE_X0_FRAC, TUBE_X1_FRAC = 882 / 2010, 1127 / 2010
    TUBE_Y0_FRAC, TUBE_Y1_FRAC = 375 / 2261, 1620 / 2261

    tube_width_px = (TUBE_X1_FRAC - TUBE_X0_FRAC) * W
    tube_cx_px = (TUBE_X0_FRAC + TUBE_X1_FRAC) / 2 * W
    tube_cy_px = (TUBE_Y0_FRAC + TUBE_Y1_FRAC) / 2 * H

    ancho_util = (cols - 1) * escala
    ancho_deseado_tubo = ancho_util + 1.1 * escala
    esc_px = ancho_deseado_tubo / tube_width_px

    cx = ancho_util / 2
    centro_y_datos = -(filas - 1) * escala / 2

    left = cx - tube_cx_px * esc_px
    right = cx + (W - tube_cx_px) * esc_px
    top = centro_y_datos + tube_cy_px * esc_px
    bottom = centro_y_datos - (H - tube_cy_px) * esc_px
    return left, right, bottom, top, img


def _dibujar_avion_vector(ax, filas, cols, escala, ruta_imagen):
    left, right, bottom, top, img = _calcular_extent_vector(filas, cols, escala, ruta_imagen)
    ax.imshow(img, extent=(left, right, bottom, top), zorder=0, origin="upper")

    col_pasillo = cols // 2
    ax.add_patch(patches.Rectangle(
        (col_pasillo * escala - 0.45 * escala, bottom),
        0.9 * escala, top - bottom,
        facecolor=COLOR_PASILLO, alpha=0.55, zorder=0.5, edgecolor="none",
    ))
    return left, right, bottom, top


def render_frame(ax, matriz_actual, matriz_anterior, paso, total_pasos, titulo, escala=1.0,
                  fuselaje_vector=None):
    ax.clear()
    filas, cols = matriz_actual.shape
    col_pasillo = cols // 2

    if fuselaje_vector is not None:
        limites = _dibujar_avion_vector(ax, filas, cols, escala, fuselaje_vector)
    else:
        _dibujar_avion_esquematico(ax, filas, cols, escala)
        limites = None

    x_pasillo = col_pasillo * escala
    for f in range(filas):
        y = -f * escala
        for c in range(cols):
            x = c * escala
            if c == col_pasillo:
                if matriz_actual[f, col_pasillo] == 1:
                    _dibujar_persona_pasillo(ax, x_pasillo, y, escala)
                continue
            estado = _estado_de_asiento(f, c, matriz_actual, matriz_anterior)
            _dibujar_asiento(ax, x, y, estado, escala)
        ax.text(-0.85 * escala, y, str(f + 1), fontsize=7, ha="right", va="center", color="#555")

    ancho_util = (cols - 1) * escala
    if limites is not None:
        left, right, bottom, top = limites
        ax.set_xlim(left - 0.2 * escala, right + 0.2 * escala)
        ax.set_ylim(bottom - 0.2 * escala, top + 0.2 * escala)
    else:
        ax.set_xlim(-1.3 * escala, ancho_util + 1.3 * escala)
        ax.set_ylim(-filas * escala - 1.4 * escala, 1.6 * escala)
    ax.set_aspect("equal")
    ax.axis("off")

    ocupados = int(matriz_actual.sum())
    total = filas * (cols - 1)
    ax.set_title(
        f"{titulo}\nPaso {paso}/{total_pasos}   ·   {ocupados}/{total} pasajeros sentados",
        fontsize=12, fontweight="bold", color="#263238",
    )


def _crear_escena(ax, filas, cols, escala, fuselaje_vector, titulo):
    """Dibuja todo lo que NO cambia (fuselaje, asientos, números de fila) y
    devuelve los artistas que sí cambian cuadro a cuadro. Así la animación no
    tiene que volver a crear ~300 figuras por cada uno de los cientos de
    cuadros, que es lo que la hacía tan lenta."""
    col_pasillo = cols // 2

    if fuselaje_vector is not None:
        left, right, bottom, top = _dibujar_avion_vector(ax, filas, cols, escala, fuselaje_vector)
        ax.set_xlim(left - 0.2 * escala, right + 0.2 * escala)
        ax.set_ylim(bottom - 0.2 * escala, top + 0.2 * escala)
    else:
        _dibujar_avion_esquematico(ax, filas, cols, escala)
        ax.set_xlim(-1.3 * escala, (cols - 1) * escala + 1.3 * escala)
        ax.set_ylim(-filas * escala - 1.4 * escala, 1.6 * escala)

    asientos = dict()
    pasillo = dict()
    for f in range(filas):
        y = -f * escala
        for c in range(cols):
            x = c * escala
            if c == col_pasillo:
                pasillo[f] = _crear_persona_pasillo(ax, x, y, escala)
            else:
                asientos[(f, c)] = _crear_asiento(ax, x, y, escala)
        ax.text(-0.85 * escala, y, str(f + 1), fontsize=7, ha="right", va="center", color="#555")

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(titulo, fontsize=12, fontweight="bold", color="#263238")
    return asientos, pasillo


def _actualizar_escena(ax, asientos, pasillo, matriz_actual, matriz_anterior,
                       paso, total_pasos, titulo):
    """Actualiza los colores y la visibilidad de los artistas ya creados."""
    filas, cols = matriz_actual.shape
    col_pasillo = cols // 2

    for (f, c), artistas in asientos.items():
        _pintar_asiento(artistas, _estado_de_asiento(f, c, matriz_actual, matriz_anterior))

    for f, artistas in pasillo.items():
        visible = matriz_actual[f, col_pasillo] == 1
        for artista in artistas:
            artista.set_visible(visible)

    ocupados = int(matriz_actual.sum())
    total = filas * (cols - 1)
    ax.title.set_text(
        f"{titulo}\nPaso {paso}/{total_pasos}   ·   {ocupados}/{total} pasajeros sentados"
    )


def _armar_leyenda(fig):
    """Se llama UNA sola vez (no en cada cuadro): fig.legend() no se borra
    con ax.clear(), así que no hace falta reconstruirla por cuadro."""
    legend_items = [
        patches.Patch(facecolor=COLOR_LIBRE, edgecolor=COLOR_BORDE_LIBRE, label="Asiento libre"),
        patches.Patch(facecolor=COLOR_NUEVO, edgecolor=COLOR_BORDE_NUEVO, label="Se acaba de sentar"),
        patches.Patch(facecolor=COLOR_OCUPADO, edgecolor=COLOR_BORDE_OCUPADO, label="Ya sentado"),
        patches.Patch(facecolor=COLOR_CAMINANDO, edgecolor=COLOR_BORDE_CAMINANDO, label="Caminando"),
    ]
    fig.legend(handles=legend_items, loc="lower center", ncol=2, fontsize=8, frameon=False)


# ============================================================
# 3. Función pública: recibe el .txt, guarda el GIF en resultados/visualizaciones
# ============================================================

def animar_embarque(ruta_txt, nombre_salida=None, titulo="Embarque del avión",
                     fps=10, escala=1.0, repeat_last=6,
                     fuselaje_vector=FUSELAJE_VECTOR_DEFAULT,
                     carpeta_resultados=None, saltar_pasos=1):
    """
    Genera la animación del embarque a partir del .txt de la simulación.

    Parámetros
    ----------
    ruta_txt : str | Path
        Ruta al .txt con el historial de matrices (el que graba
        ambiente_fisico.py).
    nombre_salida : str, opcional
        Nombre del archivo GIF a generar (por ejemplo "steffen.gif"). Si no
        se pasa, se usa el nombre del .txt de entrada con extensión .gif.
    titulo : str
        Título a mostrar arriba de la animación (por ejemplo el nombre de
        la política de embarque).
    fps : int
        Cuadros por segundo del GIF.
    escala : float
        Tamaño relativo de los asientos.
    repeat_last : int
        Cuadros extra repitiendo el último estado, para que el GIF no corte
        de golpe al terminar.
    fuselaje_vector : str | None
        Ruta a la silueta del avión a usar como fuselaje. Por default usa la
        que viene con este módulo (analisis/assets/avion_vector.png). Pasar
        None para usar el fuselaje esquemático simple en su lugar.
    carpeta_resultados : str | Path | None
        Carpeta raíz de resultados; el GIF se guarda dentro de
        "<carpeta_resultados>/visualizaciones/" (se crea si no existe).
        Por defecto, la carpeta resultados/ del repositorio.
    saltar_pasos : int
        Si la simulación tiene muchísimos pasos (por ejemplo, con la
        caminata por el pasillo contando un paso por cada fila recorrida),
        usar saltar_pasos=2 (o más) para tomar 1 de cada N estados y generar
        el GIF más rápido, sin perder demasiada fluidez visual.

    Devuelve
    --------
    str : la ruta del GIF generado.
    """
    # Si no nos dicen dónde guardar, usamos la carpeta resultados/ del repo
    if carpeta_resultados is None:
        carpeta_resultados = rutas.RESULTADOS

    ruta_txt = Path(ruta_txt)
    historial_completo = parsear_historial(ruta_txt)
    historial = historial_completo[::saltar_pasos]
    if historial[-1] is not historial_completo[-1]:
        historial.append(historial_completo[-1])  # no perderse el estado final

    carpeta_viz = Path(carpeta_resultados) / "visualizaciones"
    carpeta_viz.mkdir(parents=True, exist_ok=True)

    if nombre_salida is None:
        nombre_salida = ruta_txt.stem + ".gif"
    ruta_salida = carpeta_viz / nombre_salida

    frames = historial + [historial[-1]] * repeat_last
    total_pasos = len(historial)
    filas, cols = historial[0].shape

    if fuselaje_vector is not None:
        left, right, bottom, top, _ = _calcular_extent_vector(filas, cols, escala, fuselaje_vector)
        alto_fig = 8.0
        ancho_fig = alto_fig * ((right - left) / (top - bottom))
    else:
        alto_fig, ancho_fig = max(6, filas * 0.32), 4.8

    fig, ax = plt.subplots(figsize=(ancho_fig, alto_fig))
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(bottom=0.08)  # deja lugar para la leyenda fija
    _armar_leyenda(fig)

    # Creamos la escena una sola vez y después solo le cambiamos los colores
    asientos, pasillo = _crear_escena(ax, filas, cols, escala, fuselaje_vector, titulo)

    def update(i):
        actual = frames[i]
        anterior = frames[i - 1] if i > 0 else None
        paso_mostrado = min(i + 1, total_pasos)
        _actualizar_escena(ax, asientos, pasillo, actual, anterior,
                           paso_mostrado, total_pasos, titulo)

    anim = FuncAnimation(fig, update, frames=len(frames), interval=1000 / fps)
    anim.save(str(ruta_salida), writer=PillowWriter(fps=fps), dpi=90)
    plt.close(fig)

    print(f"GIF guardado en: {ruta_salida}  ({len(frames)} cuadros, {total_pasos} pasos mostrados "
          f"de {len(historial_completo)} pasos totales de la simulación)")
    return str(ruta_salida)
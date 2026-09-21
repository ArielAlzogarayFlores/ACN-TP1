"""
Visualizador de embarque de avión.

Toma una secuencia (historial) de matrices de asientos (25 filas x 5 columnas,
columna del medio = pasillo, 1 = ocupado, 0 = libre) y genera una animación
en GIF donde se ve el avión, los asientos, y a la gente sentándose paso a paso.

Uso básico:
    from visualizador_embarque import animar_embarque
    animar_embarque(historial, "mi_embarque.gif", titulo="Política Back-to-Front")

Donde `historial` es una lista de arrays numpy de forma (25, 5), uno por cada
paso de la simulación (el estado de la matriz en ese instante).
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter

# ---------- Paleta de colores (pensada para que se distinga fácil) ----------
COLOR_LIBRE = "#E8F5E9"       # verde clarito = asiento vacío
COLOR_BORDE_LIBRE = "#81C784"
COLOR_OCUPADO = "#64B5F6"     # azul = ya sentado hace rato
COLOR_BORDE_OCUPADO = "#1976D2"
COLOR_NUEVO = "#FFB74D"       # naranja = se acaba de sentar en ESTE paso
COLOR_BORDE_NUEVO = "#E65100"
COLOR_PASILLO = "#F5F5F5"
COLOR_FUSELAJE = "#37474F"
COLOR_CAMINANDO = "#AB47BC"   # violeta = persona parada/caminando en el pasillo
COLOR_BORDE_CAMINANDO = "#6A1B9A"


def _dibujar_avion(ax, filas, cols_por_lado, escala=1.0):
    """Dibuja el contorno del avión (fuselaje, nariz y cola) como fondo."""
    ancho_total = (2 * cols_por_lado + 1) * escala  # +1 por el pasillo
    alto_total = filas * escala

    # Fuselaje: rectángulo redondeado
    fuselaje = patches.FancyBboxPatch(
        (-0.6 * escala, -alto_total),
        ancho_total + 0.2 * escala, alto_total + 0.6 * escala,
        boxstyle="round,pad=0,rounding_size=0.35",
        linewidth=2.5, edgecolor=COLOR_FUSELAJE, facecolor="white", zorder=0,
    )
    ax.add_patch(fuselaje)

    # Nariz del avión (arriba, fila 0)
    cx = ancho_total / 2 - 0.6 * escala
    nariz = patches.Polygon(
        [(cx - ancho_total / 2 - 0.1, 0.3 * escala),
         (cx + ancho_total / 2 + 0.1, 0.3 * escala),
         (cx, 1.3 * escala)],
        closed=True, facecolor=COLOR_FUSELAJE, zorder=0,
    )
    ax.add_patch(nariz)

    # Cola del avión (abajo)
    cola = patches.Rectangle(
        (cx - 0.35 * escala, -alto_total - 1.1 * escala),
        0.7 * escala, 0.8 * escala,
        facecolor=COLOR_FUSELAJE, zorder=0,
    )
    ax.add_patch(cola)

    # Franja del pasillo (visual, para que se note el corredor)
    col_pasillo_x = cols_por_lado * escala - 0.1 * escala
    ax.add_patch(patches.Rectangle(
        (col_pasillo_x, -alto_total - 0.1 * escala),
        escala + 0.2 * escala, alto_total + 0.2 * escala,
        facecolor=COLOR_PASILLO, zorder=0.5,
    ))


def _dibujar_asiento(ax, x, y, estado, escala=1.0):
    """
    Dibuja un asiento en (x, y). estado en {"libre", "ocupado", "nuevo"}.
    Si está ocupado, dibuja también un muñequito simple adentro.
    """
    color_map = {
        "libre": (COLOR_LIBRE, COLOR_BORDE_LIBRE),
        "ocupado": (COLOR_OCUPADO, COLOR_BORDE_OCUPADO),
        "nuevo": (COLOR_NUEVO, COLOR_BORDE_NUEVO),
    }
    face, edge = color_map[estado]
    tam = 0.8 * escala

    ax.add_patch(patches.FancyBboxPatch(
        (x - tam / 2, y - tam / 2), tam, tam,
        boxstyle="round,pad=0,rounding_size=0.12",
        linewidth=1.8, edgecolor=edge, facecolor=face, zorder=2,
    ))

    if estado in ("ocupado", "nuevo"):
        # Muñequito simple: cabeza (círculo) + cuerpo (triángulo/trapecio)
        ax.add_patch(patches.Circle((x, y + 0.16 * escala), 0.13 * escala,
                                     facecolor="#4E342E", zorder=3))
        cuerpo = patches.FancyBboxPatch(
            (x - 0.18 * escala, y - 0.28 * escala), 0.36 * escala, 0.3 * escala,
            boxstyle="round,pad=0,rounding_size=0.08",
            facecolor=edge, edgecolor="none", zorder=3,
        )
        ax.add_patch(cuerpo)


def _dibujar_persona_pasillo(ax, x, y, escala=1.0):
    """Dibuja el muñequito de alguien parado/caminando en el pasillo (violeta,
    para diferenciarlo claramente de alguien ya sentado en un asiento)."""
    # halo sutil para que se note que está "en movimiento", no en un asiento
    ax.add_patch(patches.Circle((x, y), 0.34 * escala, facecolor=COLOR_CAMINANDO,
                                 edgecolor=COLOR_BORDE_CAMINANDO, linewidth=1.5,
                                 alpha=0.35, zorder=3))
    ax.add_patch(patches.Circle((x, y + 0.14 * escala), 0.12 * escala,
                                 facecolor="#4E342E", zorder=4))
    cuerpo = patches.FancyBboxPatch(
        (x - 0.15 * escala, y - 0.24 * escala), 0.3 * escala, 0.28 * escala,
        boxstyle="round,pad=0,rounding_size=0.07",
        facecolor=COLOR_BORDE_CAMINANDO, edgecolor="none", zorder=4,
    )
    ax.add_patch(cuerpo)


def _estado_de_asiento(fila, col, matriz_actual, matriz_anterior):
    if matriz_actual[fila, col] == 0:
        return "libre"
    if matriz_anterior is None or matriz_anterior[fila, col] == 0:
        return "nuevo"
    return "ocupado"


def render_frame(ax, matriz_actual, matriz_anterior, paso, total_pasos, titulo, escala=1.0):
    ax.clear()
    filas, cols = matriz_actual.shape
    col_pasillo = cols // 2
    cols_por_lado = col_pasillo  # asientos a cada lado del pasillo

    _dibujar_avion(ax, filas, cols_por_lado, escala)

    x_pasillo = col_pasillo * escala + 0.5 * escala

    for f in range(filas):
        y = -f * escala
        for c in range(cols):
            if c == col_pasillo:
                if matriz_actual[f, col_pasillo] == 1:
                    _dibujar_persona_pasillo(ax, x_pasillo, y, escala)
                continue
            x = c * escala if c < col_pasillo else (c) * escala + escala  # deja hueco del pasillo
            estado = _estado_de_asiento(f, c, matriz_actual, matriz_anterior)
            _dibujar_asiento(ax, x, y, estado, escala)
        # número de fila a la izquierda
        ax.text(-0.85 * escala, y, str(f + 1), fontsize=7, ha="right", va="center", color="#555")

    ax.set_xlim(-1.3 * escala, (cols) * escala + 0.8 * escala)
    ax.set_ylim(-filas * escala - 1.4 * escala, 1.6 * escala)
    ax.set_aspect("equal")
    ax.axis("off")

    ocupados = int(matriz_actual.sum())
    total = filas * (cols - 1)
    ax.set_title(
        f"{titulo}\nPaso {paso}/{total_pasos}   ·   {ocupados}/{total} pasajeros sentados",
        fontsize=12, fontweight="bold", color="#263238",
    )

    # Leyenda
    legend_items = [
        patches.Patch(facecolor=COLOR_LIBRE, edgecolor=COLOR_BORDE_LIBRE, label="Asiento libre"),
        patches.Patch(facecolor=COLOR_NUEVO, edgecolor=COLOR_BORDE_NUEVO, label="Se acaba de sentar"),
        patches.Patch(facecolor=COLOR_OCUPADO, edgecolor=COLOR_BORDE_OCUPADO, label="Ya sentado"),
        patches.Patch(facecolor=COLOR_CAMINANDO, edgecolor=COLOR_BORDE_CAMINANDO, label="Caminando"),
    ]
    ax.legend(handles=legend_items, loc="upper center", bbox_to_anchor=(0.5, 0.015),
              ncol=2, fontsize=8, frameon=False)


def animar_embarque(historial, filename="embarque.gif", titulo="Embarque del avión",
                     fps=2, escala=1.0, repeat_last=6):
    """
    Genera un GIF animado a partir del historial de matrices de asientos.

    Parámetros
    ----------
    historial : list[np.ndarray]
        Lista de matrices (filas x columnas) de 0s y 1s, una por cada paso
        de la simulación.
    filename : str
        Ruta donde guardar el GIF.
    titulo : str
        Título a mostrar (por ejemplo, el nombre de la política: "Steffen", etc).
    fps : int
        Cuadros por segundo del GIF (más bajo = más lento / más fácil de seguir).
    escala : float
        Tamaño relativo de los asientos (no suele hacer falta tocarlo).
    repeat_last : int
        Cuántos cuadros extra repetir al final (para que el GIF haga una
        pausa visible cuando termina el embarque, en vez de cortar de golpe).
    """
    historial = [np.asarray(m) for m in historial]
    frames = historial + [historial[-1]] * repeat_last
    total_pasos = len(historial)

    filas, cols = historial[0].shape
    alto_fig = max(6, filas * 0.28)
    fig, ax = plt.subplots(figsize=(4.5, alto_fig))
    fig.patch.set_facecolor("white")

    def update(i):
        actual = frames[i]
        anterior = frames[i - 1] if i > 0 else None
        paso_mostrado = min(i + 1, total_pasos)
        render_frame(ax, actual, anterior, paso_mostrado, total_pasos, titulo, escala)

    anim = FuncAnimation(fig, update, frames=len(frames), interval=1000 / fps)
    anim.save(filename, writer=PillowWriter(fps=fps))
    plt.close(fig)
    print(f"GIF guardado en: {filename}  ({len(frames)} cuadros, {total_pasos} pasos de simulación)")
    return filename
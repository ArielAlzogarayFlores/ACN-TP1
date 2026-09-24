# Aplicaciones Computacionales en Negocios — Trabajo Práctico N°1

Este repositorio contiene todo el código fuente correspondiente al *Trabajo Práctico N°1* de la materia de *Aplicaciones Computacionales en Negocios*.

## Estructura del repositorio

A continuación, la estructura del repositorio:

```text
.
├── analisis/
│   ├── assets/
│   │   └── avion_vector.png   # Imagen del avión usada en la animación
│   ├── estadisticas.py        # Funciones de cálculo de estadísticas respecto a las simulaciones
│   ├── bonus_estadisticas.py  # Simulaciones con el agente bonus (p = 0.8), guardadas aparte de las del modelo base
│   ├── lectura_resultados.py  # Lectura de los archivos de resultados generados por las simulaciones
│   └── animacion.py           # Función para visualizar una animación del embarque del avión
|
├── notebooks/
│   └── desarrollo.ipynb       # Análisis de las simulaciones, resultados finales, gráficos y bonus (resolución del TP)
| 
├── resultados/                # Archivos .txt con los resultados de las simulaciones
│   ├── grandes_simulaciones/       # Resultados del modelo base, un archivo por cada valor de p
│   ├── grandes_simulaciones_bonus/ # Resultados del modelo con el agente bonus
│   ├── simulaciones/               # Registro paso a paso de las simulaciones animadas
│   └── visualizaciones/            # Animaciones (.gif) del embarque
|
├── simulacion/
│   ├── ambiente_fisico.py     # Representación del avión como espacio físico: filas, asientos, métodos de abordaje, pasillo y unidades de tiempo (reloj)
│   ├── agente.py              # Estado, acciones y reglas de comportamiento e interacción de los pasajeros
│   ├── bonus_agente.py        # Variante del pasajero con velocidades heterogéneas según su grupo (bonus)
│   └── runner.py              # Corre N simulaciones y devuelve resultados
│
├── .gitignore
├── ACN_TP1_consigna.pdf    
├── ACN_TP1_presentación.pdf   # Slides de la presentación del trabajo realizado
├── README.md
├── rutas.py                   # Rutas del proyecto, para ejecutar el código desde cualquier directorio
└── requirements.txt           # Dependencias del proyecto
```

## Replicabilidad del entorno

Como bien delimita la consigna, en el proyecto utilizamos **Python** y Jupyter Notebooks.

Para instalar las dependencias utilizando un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
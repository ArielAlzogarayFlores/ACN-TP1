# Aplicaciones Computacionales en Negocios — Trabajo Práctico N°1

Este repositorio contiene todo el código fuente correspondiente al *Trabajo Práctico N°1* de la materia de *Aplicaciones Computacionales en Negocios*.

## Estructura del repositorio

A continuación, la estructura del repositorio:

```text
.
├── analisis/
│   ├── estadisticas.py        # Funciones de cálculo de estadísticas respecto a las simulaciones
|   ├── graficos.py            # Funciones de visualizaciones gráficas
│   └── animacion.py           # Función para visualizar una animación del embarque del avión
|
├── notebooks/
│   ├── principal.ipynb        # Análisis de las simulaciones, resultados finales y gráficos (resolución del TP)
│   └── bonus.ipynb            # Exploración e investigación adicional (bonus points)
| 
├── resultados/                # Archivos .txt con los resultados de las simulaciones
|
├── simulacion/
│   ├── ambiente_fisico.py     # Representación del avión como espacio físico: filas, asientos, métodos de abordaje, pasillo y unidades de tiempo (reloj)
│   ├── agente.py              # Estado, acciones y reglas de comportamiento e interacción de los pasajeros
│   └── runner.py              # Corre N simulaciones y devuelve resultados
│
├── .gitignore
├── ACN_TP1_consigna.pdf    
├── ACN_TP1_presentación.pdf   # Slides de la presentación del trabajo realizado
├── README.md
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
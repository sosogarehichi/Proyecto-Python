# Encuest.AR - Trabajo Integrador 2025

Este proyecto fue desarrollado como parte del Trabajo Integrador del Seminario de Lenguajes (Opción Python) en 2025. El objetivo es construir una aplicación de visualización de datos basada en la Encuesta Permanente de Hogares (EPH).

## Descripción

Encuest.AR permite:
- Procesar y unificar archivos EPH de hogares e individuos.
- Generar estadísticas e indicadores clave para el análisis socioeconómico.

## Funcionalidades

- Limpieza y traducción de columnas clave (sexo, educación, condición laboral, etc.).
- Cálculo de indicadores (condición de habitabilidad, tipo de hogar, materialidad).
- Procesamiento de múltiples trimestres para construir datasets consolidados.
- Visualización mediante Streamlit con navegación por secciones.

## Estructura del proyecto

```
encuestar/
├── data/                          # Archivos EPH originales (TXT)
│   └── usu_hogar_TXXX.txt
│   └── usu_individual_TXXX.txt
│
├── merge/                         # Archivos unificados (CSV)
│   └── merge_hogar.csv
│   └── merge_individual.csv
│
├── notebooks/                     # Jupyter Notebooks
│   └── procesamiento_hogares.ipynb
│   └── procesamiento_individuos.ipynb
│
├── src/                           # Lógica de procesamiento y funciones auxiliares
│   ├── procesamiento_hogar.py
│   ├── procesamiento_individual.py
│   └── unificacion.py
│
├── streamlit_app/                # Aplicación Streamlit
│   ├── inicio.py                 # Página principal
│   └── pages/                    # Navegación por secciones
│       ├── 02_carga_datos.py
│       ├── 03_busqueda_por_tema.py
│       └── 04_visualizacion.py
│
├── requirements.txt              # Librerías requeridas
├── README.md                     # Este archivo
└── .gitignore
```

## Requisitos

- Python 3.12.X
- Streamlit

# Crear entorno virtual

Por convención se tiene el entorno virtual dentro el repositorio y del proyecto.
Para crearlo se utiliza el comando:
python -m venv venv
- m de módulo
- 1er venv el módulo que se quiere ejecutar
- 2do venv el nombre de la carpeta en la que se van a guardar las cosas

```bash
python -m venv venv
```

# Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Ejecución

Desde la raíz del proyecto:

```bash
streamlit run streamlit_app/inicio.py
```

## Autores

- Nahir Ayelén Piancazza, Tobias Juarez Alvarez, Matias Joaquín Torres, Sofia Garehichi
- Universidad Nacional de La Plata
- Año: 2025

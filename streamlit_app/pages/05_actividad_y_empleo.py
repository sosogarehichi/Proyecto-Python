import json
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from pathlib import Path
import sys
import os

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
# aca se llama las funciones que se encargan de procesar los datos ustando utilities.funcionX()
import src.streamlit_logic.funciones_actividad_y_empleo as utilities

from src.utils import cargar_merge
from src.unificacion import dict_years_trimesters

# aca se llama las funciones que se encargan de procesar los datos
# usando utilities.funcionX()
import src.streamlit_logic.funciones_actividad_y_empleo as \
    utilities
from src.procesamiento_hogar import translate_aglom, detranslate_aglom

df_merge_individual = cargar_merge("individual")

dict_trim = st.session_state.get("dict_trim")
opciones_trim = dict_years_trimesters(df_merge_individual)

st.title("Actividad y Empleo 💼")
st.divider()

st.subheader("Tipo de empleo por aglomerado")
with st.expander('📌 Mostrar tabla de distribución de tipo de empleo por aglomerado ⛏️'):

    resultado = utilities.get_employment_type_distribution(df_merge_individual)

    st.dataframe(resultado, use_container_width=True)

st.divider()


st.subheader("Personas desocupadas por nivel educativo")
with st.expander('📌 Mostrar tabla con la cantidad de personas desocupadas por nivel educativo 🔍'):

    st.markdown(
        "Seleccioná un año y trimestre para ver la cantidad de personas desocupadas según el nivel educativo alcanzado.")

    if "df_merge_individual" not in st.session_state:
        st.warning(
            "No se encontró el DataFrame de individuos. Asegurate de haber cargado los datos previamente.")

    # Obtener años y trimestres únicos
    years = sorted(df_merge_individual["ANO4"].unique())

    # Widgets de selección
    year = st.selectbox("Año", years, index=len(years) - 1)
    quarter = st.selectbox("seleccione el trimestre: ",
                           opciones_trim[year])

    # Obtener y mostrar resultados
    result = utilities.get_unemployed_by_education(df_merge_individual, year, quarter)

    st.dataframe(result, use_container_width=True)
st.divider()


st.subheader("Tasa de Desempleo")

with st.expander('📌 Mostrar tabla y gráfico con la evolución de la desempleo 📉 '):
    # Mapeo de aglomerados con nombres
    aglom_options = {}
    for aglo_id in sorted(df_merge_individual['AGLOMERADO'].unique()):
        name_aglom = translate_aglom(aglo_id)
        if name_aglom:
            aglom_options[name_aglom] = aglo_id

    aglomerate_options = ['Todos los aglomerados'] + list(aglom_options.keys())
    nombre_seleccionado = st.selectbox(
        "Selecciona un aglomerado:", aglomerate_options)

    aglomerate = aglom_options.get(
        nombre_seleccionado) if nombre_seleccionado != 'Todos los aglomerados' else None

    # Mostrar tabla y gráfico
    utilities.unemployment_rate_evolution(df_merge_individual, aglomerate)
# start_page()
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# aca se llama las funciones que se encargan de procesar los
#  datos ustando utilities.funcionX()

st.divider()

st.subheader("Tasa de Empleo")

# Lista de años a usar en el gráfico
years = df_merge_individual['ANO4'].unique().tolist()

# lista de aglomerados a usar en el gráfico y para la selección
aglomerates = sorted(df_merge_individual['AGLOMERADO'].unique().tolist())
aglomerates = [
    translate_aglom(aglomerate) for aglomerate in aglomerates
]
aglomerate_options = [None] + aglomerates  # None para "Todos los aglomerados"

with st.expander('📌 Mostrar evolución de tasa de empleo por aglomerado 📈​'):
    aglomerate = st.selectbox(
        "Selecciona un aglomerado para ver la tasa de empleo:",
        aglomerate_options,
        format_func=lambda x: "Todos los aglomerados" if x is None else str(x)
    )

    # "Destraduce" el aglomerado a su código si es necesario
    aglomerate = detranslate_aglom(aglomerate) if aglomerate else None

    source = utilities.employment_rate_evolution(df_merge_individual, aglomerate)

    st.bar_chart(
        source,
        x="Año",
        y="Tasa de Empleo (%)",
        color="Aglomerado",
        stack=False
    )

st.divider()
st.subheader("Mapeo de tasa de empleo y desempleo por algomerado")
with st.expander("📌 Mapa de aglomerados según su tasa de empleo/desempleo🗺️🇦🇷"):

    # Esto sí evalúa la cantidad de años y trimestres únicos
    has_multiple_periods = lambda df : (len(df["ANO4"].unique()) > 1) or (len(df["TRIMESTRE"].unique()) > 1)

    if not(has_multiple_periods(df_merge_individual)):
        st.warning("⚠️Existe un solo periodo en el sistema para realizar este calculo.")
    else:
        tasa_tipo = st.selectbox(
            "Seleccione el tipo de tasa a mostrar en el mapa",
            options=["empleo", "desempleo"]
        )

        mapa = utilities.get_map_employment_unemployment_variation_by_agglomerate(df_merge_individual, dict_trim, tasa_tipo )

        st.header("Mapa de aglomerados segun su tasa", divider="red")

        st_folium(mapa, key=f"map_{tasa_tipo}", width=700, height=500)

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
# aca se llama las funciones que se encargan de procesar los datos usando 
#  utilities.funcionX()
import src.streamlit_logic.funciones_educacion as utilities
from src.utils import cargar_merge

df_merge_individual = cargar_merge("individual")

st.title("Educación 🎓")
st.divider()


def show_population_by_education_level():
    st.subheader("Cantidad de personas según nivel educativo alcanzado")



    with st.expander('📌 Mostrar tabla y gráfico con cantidad de personas'
                     ' según nivel educativo alcanzado 📊'):
        # Obtener los años disponibles
        years = sorted(df_merge_individual["ANO4"].unique())

        # Selección del año
        selected_year = st.selectbox("Seleccioná un año", years)

        # Obtener los resultados
        result = utilities.get_population_by_education_level(
            df_merge_individual, selected_year)

        if result.empty:
            st.info("No hay datos disponibles para el año seleccionado.")
            return

        # Mostrar tabla
        st.dataframe(result, use_container_width=True)

        # Muestro un grafico para agregar otra manera
        # de representar esos datos.
        st.bar_chart(result.set_index("Nivel educativo")["Cantidad de personas"])
    st.divider()


def start_page():

    # Cargo la lista de los años de merge ordenados.
    st.subheader("Alfabetismo 📚")
    with st.expander('📌 Mostrar gráfico de alfabetismo por año 📊'):
        utilities.alfabetismo(df_merge_individual)
    st.divider()


show_population_by_education_level()

start_page()

st.subheader("Aglomerados con estudiantes universitarios/superiores")
with st.expander(
    '📌 Mostrar Ranking de los 5 aglomerados con mayor porcentaje '
    'de hogares con dos o más ocupantes con estudios universitarios o '
    'superiores finalizados 🎓'
):
    top5 = utilities.show_top5_agglomerates_by_educated_households(df_merge_individual)
    st.dataframe(top5, hide_index=True)
    st.download_button(
        label="📥 Descargar resultados como CSV",
        data=top5.to_csv(index=False, sep=";", encoding="utf-8"),
        file_name="top5_viviendas_con_mayor_porcentaje.csv",
        mime="text/csv"
    )
    

st.divider()
st.subheader("Nivel educacional mas comun")
with st.expander("📌 Nivel educacional alcanzado mas comun"):

    modal_education = utilities.analyze_education_by_age_group(df_merge_individual)

    available_groups = modal_education.index.tolist()

    selected_groups = st.multiselect(
        "Rango(s) etario(s) a visualizar:",
        options=available_groups,
        default=available_groups[0]
    )

    resultado_filtrado = modal_education.loc[selected_groups]

    st.subheader("🏫 Nivel educativo más frecuente por grupo etario")
    for grupo_etario, nivel_educativo in resultado_filtrado.items():
        st.markdown(f"🔹 En el grupo **{grupo_etario}**, el nivel educativo más frecuente es **{nivel_educativo}**.")

    st.subheader("Visualización por grupo etario")
    st.bar_chart(resultado_filtrado)

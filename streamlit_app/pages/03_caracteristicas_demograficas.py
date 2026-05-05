from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
import src.streamlit_logic.funciones_caracteristicas_demograficas as utils
import src.streamlit_logic.funciones_caracteristicas_demograficas as utilities
from src.utils import cargar_merge
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# df_merge_individual = st.session_state.get("df_merge_individual") or cargar_merge("individual")
df_merge_individual = cargar_merge("individual")

dict_trim = st.session_state.get("dict_trim", {})

# en el estado de la pagina busco los años que se registraron
years_available = list(dict_trim.keys())

st.title("Características Demográficas 🗺️​")

st.subheader("Evolución de la Tasa de Dependencia Demográfica")
with st.expander('📌 Mostrar tabla de tasa de dependencia demográfica 📋​'):
    st.subheader("Tasa de dependencia demográfica")
    st.markdown(
        """
        Esta visualización muestra cómo ha evolucionado la tasa de dependencia demográfica
        a lo largo del tiempo, para un aglomerado seleccionado.
        """
    )
    
    # Obtener resultados del backend
    df_dependency = utils.calculate_dependency_evolution(df_merge_individual)

    # Obtener lista de aglomerados disponibles
    aglos_disponibles = sorted(df_dependency["Aglomerado"].unique())
    aglo_elegido = st.selectbox("Seleccioná un aglomerado:", aglos_disponibles)

    # Filtrar los datos por el aglomerado seleccionado
    df_filtrado = df_dependency[df_dependency["Aglomerado"] == aglo_elegido]

    if df_filtrado.empty:
        st.info("ℹ️ No hay datos para este aglomerado.")
        

    # Mostrar columna como texto con el símbolo %
    df_filtrado["Tasa de dependencia"] = df_filtrado["Tasa de dependencia"].astype(str) + "%"

    # Mostrar en tabla
    st.subheader("📋 Tasa de dependencia demográfica (tabla)")
    st.dataframe(df_filtrado[["Año", "TRIMESTRE", "Tasa de dependencia"]], use_container_width=True, hide_index=True)


st.divider()
st.subheader("Edad promedio por aglomerado")
with st.expander('📌 Mostrar tabla de edad promedio por aglomerado 👤'):
    st.markdown(
        "Este informe muestra la edad promedio por aglomerado para el último año y trimestre disponibles."
    )

    result = utils.get_avg_age_by_agglomerate(df_merge_individual)

    # Redondear y convertir a entero
    result["Edad promedio"] = result["Edad promedio"].round(0).astype(int)

    # Mostrar tabla con el nombre del aglomerado como índice
    st.dataframe(result.set_index("aglomerado"), use_container_width=True)


st.divider()
st.subheader("Media y mediana de la edad")
with st.expander('📌 Mostrar tabla de edad media y mediana por año y por trimestre 📅'):
    st.markdown(
        "Este informe muestra la media y la mediana de la edad de la población "
        "para cada año y trimestre almacenado."
    )

    result = utils.get_age_stats_by_year_trim(df_merge_individual)

    result = result.rename(columns={
        "ANO4": "Año",
        "Edad_media": "Edad media",
        "Edad_mediana": "Edad mediana"
    })

    # Mostrar tabla con índice para año y TRIMESTRE
    st.dataframe(result.set_index(
        ["Año", "TRIMESTRE"]), use_container_width=True)


st.divider()
st.subheader("Distribución de población por edad")
with st.expander('📌 Mostrar gráfica de distribución de población 👥​'):

    year = st.selectbox(
        "Seleccione el año:",
        dict_trim.keys(),
        key="mi_selectbox_year_unico"
    )
    year = int(year)  # Convertir a entero para evitar problemas de tipo
    
    trimester = st.selectbox(
        "Seleccione el trimestre:",
        df_merge_individual[(df_merge_individual["ANO4"] == year)]["TRIMESTRE"].unique(),
        key="mi_selectbox_trimestre_unico")
    
    fig = utilities.give_grafic_distribution_age_gender(df_merge_individual,
                                                        year,
                                                        trimester)

    st.pyplot(fig)

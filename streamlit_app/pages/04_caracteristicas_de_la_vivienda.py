import streamlit as st
import plotly.express as px
import json
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.utils import cargar_merge

# aca se llama las funciones que se encargan de procesar
# los datos ustando utilities.funcionY()
import src.streamlit_logic.funciones_caracteristicas_de_la_vivienda as utilities
import src.streamlit_logic.funciones_caracteristicas_de_la_vivienda as vivienda_utils

df_merge_hogar = cargar_merge("hogar")


years = df_merge_hogar['ANO4'].unique().tolist()
opciones = [None] + years  # None para "Todos los años"

st.title("Características de la Vivienda 🏠")

years = df_merge_hogar['ANO4'].unique().tolist()
years.sort()
years.insert(0, 'Todos los años')
year = st.selectbox('Selecciona el año', years, index=0)
st.divider()


def filter_by_year(df_merge_hogar_filtered: pd.DataFrame, year: str):
    if year == 'Todos los años':
        return df_merge_hogar_filtered
    else:
        return df_merge_hogar_filtered[df_merge_hogar_filtered['ANO4'] == year]


df_merge_hogar_filtered = filter_by_year(df_merge_hogar, year)


def work_for_with(df_merge_hogar_filtered: pd.DataFrame):
    years = df_merge_hogar_filtered['ANO4'].unique().tolist()
    years.sort()
    years.insert(0, 'Todos los años')
    year = st.selectbox('Selecciona el año', years, index=0)
    st.divider()
    return year


def start_page(df_merge_hogar_filtered: pd.DataFrame, year):

    aglom_options = utilities.income(df_merge_hogar_filtered)

    if 'aglo_selected' not in st.session_state:
        st.session_state.aglo_selected = None
    if 'aglo_submitted' not in st.session_state:
        st.session_state.aglo_submitted = False
    if 'aglo_selected2' not in st.session_state:
        st.session_state.aglo_selected2 = None
    if 'aglo_submitted2' not in st.session_state:
        st.session_state.aglo_submitted2 = False
    # ----- Primera muestra

    st.session_state.year_selected = year

    st.subheader('Viviendas que disponen de baño dentro del hogar 🚽')
    with st.expander('📌 Mostrar proporcion de viviendas que disponen de baño dentro del hogar 🚽'):
        utilities.proportion_bathroom(df_merge_hogar_filtered)
    st.divider()

    # ----- Segunda muestra
    st.subheader('📈 Evolucion del regimen de tenencia')
    with st.expander('📌 Mostrar evolucion del regimen de tenencia 🏘️'):
        agglomerate = st.selectbox(
            'Selecciona el aglomerado para ver la evolucion del regimen de tenencia', aglom_options, index=None)
        if agglomerate is None:
            st.warning("Por favor, selecciona un aglomerado para continuar.")
        else:
            st.session_state.aglo_selected = agglomerate
            st.session_state.aglo_submitted = True

        if st.session_state.get("aglo_submitted"):    
            with st.form("Seleccionar"):
                agglomerate_id = aglom_options[st.session_state.aglo_selected]
                tenure_options = utilities.select_tenure(df_merge_hogar_filtered, agglomerate_id)
                selected_tenures = st.multiselect(
                    "Selecciona el / los tipo de régimen de tenencia que deseas ver",
                    options=list(tenure_options.keys()),
                    default=None)
                submitted_tenencia = st.form_submit_button("Generar Evolucion")
            if submitted_tenencia:
                if not selected_tenures:
                    st.error(
                        "❌ Por favor, selecciona al menos un tipo de régimen de tenencia.")
                    return
                utilities.tenure_regime_evolution(
                    df_merge_hogar_filtered, agglomerate_id, selected_tenures)
    st.divider()
    # ----- Tercer muestra
    st.subheader('📊 Viviendas en villas de emergencia por aglomerado')
    with st.expander('📌 Mostrar la cantidad de viviendas ubicadas en villa de emergencia 🏚️'):
        aglomerado = st.selectbox(
                'Selecciona el aglomerado para ver la cantidad de viviendas ubicadas en villa de emergencia', aglom_options, index=None)

        if aglomerado is None:
            st.warning("Por favor, selecciona un aglomerado para continuar.")
        else:
            st.session_state.aglo_selected2 = aglomerado
            st.session_state.aglo_submitted2 = True
        if st.session_state.get("aglo_submitted2"):
            utilities.housing_report(df_merge_hogar_filtered)
    st.divider()


# year = work_for_with(df_merge_hogar)

# df_merge_hogar_filtered = filter_by_year(df_merge_hogar, year)

st.subheader("Viviendas encuestadas")
with st.expander("📌Mostrar cantidad total de viviendas incluidas en la encuesta para el año seleccionado."):
    # Calcular total de viviendas
    total = vivienda_utils.get_total_viviendas_por_anio(
        df_merge_hogar_filtered)

    # Mostrar el resultado
    st.success(
        f" Total de viviendas encuestadas en {year}: **{total}**")
st.divider()

start_page(df_merge_hogar_filtered, year)

st.subheader('Viviendas por tipo')
with st.expander('📌 Mostrar gráfico de porcentaje de viviendas por tipo 🏚️​'):
    fig = utilities.home_percentage_per_type(df_merge_hogar_filtered, year)
    st.pyplot(fig)

st.divider()
st.subheader("Piso Predominante por Aglomerado")
with st.expander('📌 Mostrar tabla de piso predominante por aglomerado 👞​'):
    tabla = utilities.floor_per_aglomerate(df_merge_hogar_filtered)
    st.dataframe(tabla, hide_index=True)

st.divider()
st.subheader("Condición de habitabilidad por aglomerado")
with st.expander("📌 Mostrar gráfico de porcentajes de condición de habitabilidad por aglomerado 👪"):

    st.header("Grafico de porcentajes por aglomerado", divider="gray")

    fig, df_for_download = utilities.show_visualizer_condition_percentage_by_agglomerate(df_merge_hogar_filtered)

    st.plotly_chart(fig)

    st.dataframe(df_for_download[["AGLOMERADO_NOMBRE", "CONDICION_DE_HABITABILIDAD", "PORCENTAJE"]].sort_values("AGLOMERADO_NOMBRE"))
    
    st.download_button(
        label="📥 Descargar resultados como CSV",
        data=df_for_download.to_csv(index=False, sep=";", encoding="utf-8"),
        file_name="porcentaje_viviendas_por_condicion.csv",
        mime="text/csv"
    )
    st.caption("⚠️ Si abrís el archivo con Excel, usá 'Datos → Obtener datos desde texto/CSV' y seleccioná UTF-8 como codificación.")


import streamlit as st
from pathlib import Path
import sys
import matplotlib.pyplot as plt
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# aca se llama las funciones que se encargan de procesar
# los datos ustando utilities.funcionX()
import src.streamlit_logic.funciones_ingresos as utilities
from src.unificacion import dict_years_trimesters
from src.utils import cargar_merge

df_merge_hogar = cargar_merge("hogar")

opciones = dict_years_trimesters(df_merge_hogar)

print(opciones)

st.title(" Ingresos 💰​")
st.divider()
year_selected = st.selectbox("Seleccione el año: ", list(opciones.keys()))
trim_selected = st.selectbox("seleccione el trimestre: ",
                             opciones[year_selected])

meses = utilities.trim_map(trim_selected)
st.write(f"Meses correspondientes al trimestre seleccionado: {', '.join(meses)}")

st.divider()
st.subheader("Hogares por debajo de la línea de pobreza e indigencia ")
with st.expander('📌 Mostrar resumen de cantidad y porcentaje de hogares 🔍'):
    df_completo = utilities.obtener_datos_completos_de_hogares_con_canasta_basica(
        df_merge_hogar, year_selected, trim_selected
    )
    resumen = utilities.resumen_ponderado_por_condicion(df_completo)
    resumen = resumen.rename(columns={
        "condicion": "Condición",
        "hogares_ponderados": "Hogares ponderados",
        "porcentaje_ponderado": "% ponderado"
    })
    st.subheader("Resumen ponderado por condición socioeconómica:")
    st.dataframe(resumen, use_container_width=True)
    st.divider()
    st.subheader("**Porcentaje ponderado de hogares por condición socioeconómica**")
    st.bar_chart(resumen.set_index('Condición')["% ponderado"])

with st.expander('📌 Mostrar datos completos de cantidad y '
                 'porcentaje de hogares 🧾'):
    st.subheader("Datos completos de hogares con canasta básica:")
    columnas = ["CODUSU", "ingreso_total", "equivalencia", "condicion", "año"]
    # st.dataframe(df_completo)
    st.dataframe(df_completo[columnas], use_container_width=True)
    st.divider()
    st.subheader("**Ingreso total promedio por condición socioeconómica**")
    promedios = df_completo.groupby("condicion")["ingreso_total"].mean()
    st.bar_chart(promedios)

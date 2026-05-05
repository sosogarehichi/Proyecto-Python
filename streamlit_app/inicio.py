import streamlit as st
from pathlib import Path

st.title("Encuest.AR")
st.divider()
st.write("La Encuesta Permanente de Hogares (EPH) recopila información "
         "detallada sobre las características demográficas, sociales y "
         "económicas de los hogares y las personas en centros urbanos "
         "de Argentina. Entre sus principales contenidos se encuentran datos "
         "sobre condiciones de la vivienda, estructura del hogar, educación, "
         "salud, situación laboral, ingresos laborales y no laborales, así "
         "como estrategias de subsistencia. Esta información permite analizar "
         "la distribución del ingreso, el mercado de trabajo, la pobreza y "
         "otras dimensiones clave del bienestar social.")

st.divider()
st.page_link(
    Path.cwd() / 'streamlit_app' / 'pages' / '02_carga_datos.py',
    label="Ir a carga de datos",
    icon="📥",
)

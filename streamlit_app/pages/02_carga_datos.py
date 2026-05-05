import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.procesamiento_individual import process_individual_a
from src.procesamiento_hogar import process_hogar_a
from src.unificacion import merge_data, show_range, checking_twins

st.title("Carga de Datos")

st.divider()
if st.button("Crear Dataset"):
    try:
        # defino carpetas de entrada y salida
        folder_in = Path("data")
        folder_out = Path("merge")
        # archivos de salida
        file_individual = folder_out / "merge_individual.csv"
        file_hogar = folder_out / "merge_hogar.csv"

        merge_data(folder_in, folder_out)
        st.success("✅ Merge completo")

        process_hogar_a(file_hogar)
        st.success("🏠 Análisis hogar completo.")

        # se almacena el dataframe como variable en la pagina para tener
        # una sola fuente de verdad
        if file_hogar.exists:
            st.session_state["df_merge_hogar"] = pd.read_csv(file_hogar,
                                                             delimiter=";",
                                                             encoding="utf-8")
        else:
            st.warning("Dirigirse a carga de datos para crear merge.")

        process_individual_a(file_individual)
        dict_trim = process_individual_a(file_individual)
        st.success("👤 Análisis individual completo.")

        # se almacena el dataframe como variable en la pagina para tener
        # una sola fuente de verdad
        if file_individual.exists:
            st.session_state["df_merge_individual"] = pd.read_csv(
                file_individual,
                delimiter=";",
                encoding="utf-8"
            )
        else:
            st.warning("Dirigirse a carga de datos para crear merge.")

        # aca almaceno el diccionario de años con sus trimestre en el state
        st.session_state["dict_trim"] = dict_trim
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

st.divider()
st.header("Información con la que cuenta el sistema:")
st.write(show_range())

st.divider()
st.header('Subir archivo')
file = st.file_uploader("Seleccione archivo (subir de a 1)", type=['txt'])

if file is not None:
    path_load = Path("data") / file.name
    # Verificamos si el archivo ya existe
    # si ya existe -> se da una advertencia
    # si no existe se agrega a la carpeta de salida
    if path_load.exists():
        st.warning(f"El archivo '{file.name}' ya fue cargado previamente.")
        ok = False
    else:
        try:
            with open(path_load, "wb") as f:
                f.write(file.getbuffer())
            st.success(f"Archivo '{file.name}' guardado"
                       " correctamente en 'data/'")
        except Exception as e:
            st.error(f"Ocurrió un error al guardar el archivo: {e}")


# Botón para actualizar (merge)
if st.button("Actualizar Database"):
    try:
        if file is None:
            st.warning("⚠️ No se ha seleccionado ningún archivo"
                       " para actualizar.")
        else:
            folder_in = Path("data")
            folder_out = Path("merge")
            # archivos de salida
            file_individual = folder_out / "merge_individual.csv"
            file_hogar = folder_out / "merge_hogar.csv"
            # se agrega el archivo nuevo

            merge_data(folder_in, folder_out)
            st.success("✅ Dataset actualizado desde los"
                       " archivos en 'data'")

            process_hogar_a(file_hogar)
            st.success("🏠 Análisis hogar completo.")
            process_individual_a(file_individual)
            st.success("👤 Análisis individual completo.")

    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

st.divider()
twins = checking_twins()
if len(twins) > 0:
    st.warning("⚠️ Se encontraron inconsistencias en los datos:")
    for twin in twins:
        st.warning(f"{twin}")
else:
    st.success("No se encontraron inconsistencias en los datos.")
 
st.divider()
st.page_link(
    Path.cwd() / 'streamlit_app' / 'inicio.py',
    label=" Ir a inicio",
    icon="🏠"
)

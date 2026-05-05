from pathlib import Path
import pandas as pd
import streamlit as st
import sys
import os
# sys.path.append(str(Path(__file__).resolve().parent.parent.parent))


def hola():
    st.write("hola")


def cargar_merge(nombre, carpeta="merge", sep=";", encoding="utf-8") -> pd.DataFrame:
    """
    Carga un DataFrame desde `st.session_state` o desde un archivo .csv
    ubicado en la carpeta especificada.

    Si el DataFrame correspondiente ya está almacenado en el `session_state`
    bajo la clave 'merge_{nombre}',
    lo retorna directamente. Si no está, intenta leer el archivo
    'merge_{nombre}.csv' desde disco. En caso
    exitoso, guarda el DataFrame en `session_state` y también calcula un
    diccionario con el último trimestre registrado por año, el cual
    se almacena en la clave 'dict_trim'.

    Parámetros:
    ----------
    nombre : str
        Nombre base del dataset (ejemplo: "hogar", "individual").
    carpeta : str, opcional
        Carpeta donde se espera encontrar el archivo .csv
        (por defecto, "merge").
    sep : str, opcional
        Separador de columnas en el .csv (por defecto, ";").
    encoding : str, opcional
        Encoding del archivo (por defecto, "utf-8").

    Retorna:
    -------
    pd.DataFrame o None
        El DataFrame cargado, o None si no se encuentra el archivo o
        hay un error al leerlo.
    """

    def obtener_ultimo_trimestre_por_ano(df):
        resumen = df.groupby("ANO4")["TRIMESTRE"].max().to_dict()
        return resumen

    def get_merge_path(carpeta, clave):
        """
        Obtiene la ruta del directorio actual.
        """
        path_code = Path(__file__).parent.parent
        path_merge = path_code / carpeta
        path_merge = path_merge / f"{clave}"
        return path_merge

    clave = f"merge_{nombre}"
    clave_csv = f"{clave}.csv"
    df_clave = f"df_{clave}"

    merge_path = get_merge_path(carpeta, clave_csv)

    if df_clave in st.session_state:
        return st.session_state[df_clave]

    if merge_path.exists():

        try:
            df = pd.read_csv(merge_path.resolve(), delimiter=sep,
                             encoding=encoding,
                             low_memory=False
                             )
            st.session_state[clave] = df
            st.session_state["dict_trim"] = obtener_ultimo_trimestre_por_ano(df)
            return df
        except Exception as e:
            st.error(f"Error al cargar {clave}.csv: {e}")
            return None
    else:
        st.warning(f"Error al cargar {clave}.csv: el archivo no existe en la ruta {merge_path.resolve()} \n"
                   "ve a la pagina 'carga de datos' para crear merge.")
        return None


if (__name__ == "__main__"):

    current_file_dir = Path(__file__).parent

    target_dir = current_file_dir.parent.parent.parent

    df = cargar_merge("individual")
    if df is not None:
        print(df.head())
    else:
        print("No se pudo cargar el DataFrame.")

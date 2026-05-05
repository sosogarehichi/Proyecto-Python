import pandas as pd
import streamlit as st
import sys
import folium
import json
from folium.map import Marker
from pathlib import Path
from typing import Tuple
from streamlit_folium import st_folium
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.procesamiento_hogar import translate_aglom


def get_employment_type_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula cantidad de personas ocupadas y porcentaje de empleo por aglomerado.
    """

    # Filtrar personas ocupadas
    employed_df = df[df["CONDICION_LABORAL"].str.startswith("Ocupado", na=False)]

    # Total ocupados por aglomerado
    total_employed = employed_df.groupby("AGLOMERADO").size().rename("Total ocupados")

    # Conteo por tipo de empleo (PP04A)
    employment_counts = employed_df.groupby(["AGLOMERADO", "PP04A"]).size().unstack(fill_value=0)

    # Porcentajes
    employment_pct = employment_counts.div(employment_counts.sum(axis=1), axis=0) * 100

    # Renombrar columnas
    employment_pct = employment_pct.rename(columns={
        1: "% Estatal",
        2: "% Privado",
        3: "% Otro tipo"
    })

    # Unir total con porcentajes
    result = pd.concat([total_employed, employment_pct], axis=1).reset_index()

    # Redondear y convertir a string con símbolo %
    for col in ["% Estatal", "% Privado", "% Otro tipo"]:
        result[col] = result.get(col, 0).round(1).astype(str) + "%"

    # Reemplazar códigos de aglomerado por nombre
    result["Aglomerado"] = result["AGLOMERADO"].apply(translate_aglom)

    # Reordenar columnas y eliminar AGLOMERADO
    columnas_finales = ["Aglomerado", "Total ocupados", "% Estatal", "% Privado", "% Otro tipo"]
    return result[columnas_finales]


def get_unemployed_by_education(df: pd.DataFrame, year: int, quarter: int) -> pd.DataFrame:
    """
    Informa la cantidad de personas desocupadas según nivel educativo alcanzado
    para un año y trimestre específico.

    Parámetros:
        df (pd.DataFrame): DataFrame individual con columnas CONDICION_LABORAL, ANO4, TRIMESTRE, NIVEL_ED_str.
        year (int)
        quarter (int): Trimestre a consultar.

    Retorna:
        pd.DataFrame: Cantidad de personas desocupadas por nivel educativo.
    """
    # Filtrar por año y trimestre
    df_filtered = df[(df["ANO4"] == year) & (df["TRIMESTRE"] == quarter)]

    # Filtrar personas desocupadas
    df_unemployed = df_filtered[df_filtered["CONDICION_LABORAL"] == "Desocupado"]

    # Agrupar por nivel educativo y contar
    result = (
        df_unemployed
        .groupby("NIVEL_ED_str", as_index=False)
        .size()
        .rename(columns={"size": "Cantidad de desocupados"})
        .sort_values("Cantidad de desocupados", ascending=False)
    )

    return result


def unemployment_rate_evolution(df, aglomerate=None):
    """
    Muestra la evolución de la tasa de desempleo a lo largo del tiempo.
    Si se pasa un aglomerado, filtra por ese aglomerado.
    Si no, calcula para todo el país.
    """
    resultados = []

    if aglomerate is not None:
        df = df[df['AGLOMERADO'] == aglomerate]

    for year in sorted(df['ANO4'].unique()):
        df_year = df[df['ANO4'] == year]
        employment = df_year[df_year['ESTADO'] == 1]['PONDERA'].sum()
        unemployment = df_year[df_year['ESTADO'] == 2]['PONDERA'].sum()
        total = employment + unemployment
        tasa = round((unemployment / total) * 100, 2) if total > 0 else 0
        resultados.append({
            'Año': year,
            'Tasa de Desempleo': f"{tasa:.2f}%",
            'Tasa_num': tasa  # Para graficar
        })

    tabla = pd.DataFrame(resultados)

    nombre_aglo = translate_aglom(aglomerate) if aglomerate is not None else 'Todos los aglomerados'

    st.markdown(f"### Evolución de la tasa de desempleo - {nombre_aglo}")

    # Mostrar tabla
    st.dataframe(tabla[['Año', 'Tasa de Desempleo']], use_container_width=True)

    # Mostrar gráfico
    st.bar_chart(tabla.set_index('Año')['Tasa_num'])


def employment_rate_evolution(df, aglomerate=None):
    """
    Calcula la evolución de la tasa de empleo a lo largo del tiempo.
    Si se pasa un aglomerado, filtra por ese aglomerado.
    Si no, calcula para todo el país.
    """
    # Lista para almacenar los resultados de cada año
    resultados = []

    # Filtrar por aglomerado si se proporciona
    if aglomerate is not None:
        df = df[df['AGLOMERADO'] == aglomerate]

    # Año se encuentra de menor a mayor
    for year in sorted(df['ANO4'].unique()):
        # Filtra por año
        df_year = df[df['ANO4'] == year]
        # Calcula la tasa de empleo
        empleados = df_year[df_year['ESTADO'] == 1]['PONDERA'].sum()
        desocupados = df_year[df_year['ESTADO'] == 2]['PONDERA'].sum()
        # Suma los empleados y desocupados
        total = empleados + desocupados
        # Calcula la tasa de empleo
        # Redondea a dos decimales
        # Si total es 0, la tasa es 0 para evitar división por cero
        tasa = round((empleados / total) * 100, 2) if total > 0 else 0
        # Agrega los resultados a la lista
        resultados.append({
            'Año': year,
            'Aglomerado': (
                aglomerate if aglomerate is not None else 'Total País'
            ),
            'Nombre del Aglomerado': (
                translate_aglom(aglomerate) if aglomerate is not None
                else 'Total País'
            ),
            'Tasa de Empleo (%)': tasa,
        })
    # Convierte la lista en un DataFrame
    tabla = pd.DataFrame(resultados)

    return tabla


def get_map_employment_unemployment_variation_by_agglomerate(
    df: pd.DataFrame,
    dict_trim: dict,
    tasa_tipo: str
) -> folium.Map:
    """
    Genera un mapa interactivo que muestra la variación de la tasa de empleo o desempleo por aglomerado
    entre el período más antiguo y el más reciente disponible en el conjunto de datos.

    Parámetros:
    -----------
    df : pd.DataFrame
        DataFrame con datos individuales. Se procesa internamente para calcular tasas
        de empleo y desempleo por aglomerado.
    dict_trim : dict
        Diccionario que mapea años (int) a su último trimestre disponible (int).
        Ejemplo: {2022: 4, 2023: 1}
    tasa_tipo : str
        Tipo de tasa a visualizar en el mapa. Puede ser:
            - "empleo": muestra la variación de la tasa de empleo.
            - "desempleo": muestra la variación de la tasa de desempleo.

    Retorna:
    --------
    folium.Map
        Mapa interactivo de Folium con marcadores para cada aglomerado. El color del ícono indica
        si la tasa aumentó o disminuyó entre los dos períodos comparados.

    Notas:
    ------
    - Verde: tasa positiva (sube empleo o baja desempleo).
    - Rojo: tasa negativa (baja empleo o sube desempleo).
    - El popup muestra el nombre del aglomerado y el cambio porcentual.
    - El mapa se genera combinando `get_diff_rate` y `display_map`, y puede integrarse con Streamlit mediante `st_folium`.
    """
    json_path = get_json_path()
    geo_json = get_geo_json(json_path)    
    df_diff_rate = get_diff_rate(df, dict_trim)
    mapa = display_map(df_diff_rate, geo_json, tasa_tipo)    
    return mapa

def get_json_path():
    path_code = Path(__file__).parent.parent.parent
    path_data = path_code / "data"
    path_json = path_data / "aglomerados_coordenadas.json"
    return path_json

    
def get_geo_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_diff_rate(data_frame: pd.DataFrame, dict_trim: dict) -> pd.DataFrame:
    """
    Calcula la variación de tasas de empleo y desempleo entre dos trimestres para cada aglomerado.

    Esta función identifica el trimestre más antiguo y el más reciente disponible en el dataset,
    calcula las tasas de empleo y desempleo para ambos periodos, y devuelve un DataFrame con la
    diferencia entre ellos, a nivel de aglomerado.

    Parámetros:
    ----------
    data_frame : pd.DataFrame
        Dataset con los datos individuales completos. Debe incluir columnas como 'ANO4', 'TRIMESTRE',
        'PONDERA', 'ESTADO', 'AGLOMERADO', entre otras necesarias para calcular las tasas.
    dict_trim : dict
        Diccionario que mapea años a su último trimestre disponible. Por ejemplo: {2022: 4, 2023: 1}.

    Retorna:
    -------
    pd.DataFrame
        DataFrame con una fila por aglomerado e indicadores de diferencia de tasas:
        - 'DIF_TASA_EMPLEO'
        - 'DIF_TASA_DESEMPLEO'
    """

    # Obtener el periodo más reciente y el más antiguo
    old_period, new_period = get_old_new_period(data_frame, dict_trim)
            
    # Obtener las tasas de empleo y desempleo para los periodos seleccionados
    df_old, df_new = employment_and_unemployment_rate(data_frame, old_period, new_period)
    
    # Calcular las tasas entre dos momentos del tiempo, para cada aglomerado.
    resultado = calculate_diff_rate(df_old, df_new)
    
    return resultado
        
        
def get_old_new_period(df: pd.DataFrame, dict_trim: dict) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Retorna los periodos extremos (más antiguo y más reciente) disponibles en los datos.

    Esta función extrae dos pares (año, trimestre):
    - El periodo más antiguo se obtiene a partir de los datos presentes en el DataFrame `df`,
    identificando el año mínimo en la columna 'ANO4' y su trimestre más bajo en 'TRIMESTRE'.
    - El periodo más reciente se determina a partir del diccionario `dict_trim`, que contiene
    el último trimestre registrado por año, usando el año más alto como referencia.

    Parámetros:
    ----------
    df : pd.DataFrame
        DataFrame que contiene las columnas 'ANO4' (año) y 'TRIMESTRE' (trimestre).
    dict_trim : dict[str, int]
        Diccionario que mapea cada año (como string) a su último trimestre disponible.

    Retorna:
    -------
    tuple[tuple[int, int], tuple[int, int]]
        Una tupla doble con el formato:
        ((año_antiguo, trimestre_antiguo), (año_reciente, trimestre_reciente))

    Lanza:
    -----
    ValueError:
        Si el diccionario está vacío o si las columnas del DataFrame no tienen datos válidos.
    """

    if not dict_trim:
        raise ValueError("dict_trim está vacío.")
    if df["ANO4"].dropna().empty or df["TRIMESTRE"].dropna().empty:
        raise ValueError("El DataFrame no tiene datos válidos en ANO4 o TRIMESTRE.")
    
    new = get_newest_period(dict_trim)
    old = get_oldest_period(df)
    return old, new


def get_newest_period(dict_trim: dict) -> tuple[int, int]:
    year = max(dict_trim.keys())  # ya son enteros
    quarter = dict_trim[year]
    return int(year), int(quarter)


def get_oldest_period(df: pd.DataFrame) -> tuple[int, int]:
    year = df["ANO4"].min()
    quarter = df[(df["ANO4"] == year)]["TRIMESTRE"].unique().min()
    #quarter = df.query("ANO4 == @old_year", engine="numexpr")["TRIMESTRE"].min()
    return year, quarter


def employment_and_unemployment_rate(
            df: pd.DataFrame, old_period: tuple, new_period: tuple
        ) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calcula y retorna las tasas de empleo y desempleo por aglomerado.

    Filtra el DataFrame por período, selecciona personas activas, agrupa
    por aglomerado y calcula la PEA, ocupados y desocupados. Finalmente,
    calcula las tasas de empleo y desempleo para cada período.

    Parámetros:
        df (pd.DataFrame): DataFrame con los datos individuales.
        old_period (tuple): Año y Trimestre del período mas viejo.
        new_period (tuple): Año y Trimestre del período mas reciente.
    
    Retorna:
        Tuple[pd.DataFrame, pd.DataFrame]: Dos DataFrames con las tasas
        de empleo y desempleo por aglomerado para cada período.
    """
   
    # Lógica principal de la función
    old_year, old_quarter = old_period
    new_year, new_quarter = new_period
    
    df_merged_old = process_period(df, old_year, old_quarter)
    df_merged_new = process_period(df, new_year, new_quarter)
    
    return df_merged_old, df_merged_new 

def process_period(df: pd.DataFrame, year: int, quarter: int) -> pd.DataFrame:
    df_period = filter_by_year_and_quarter(df, year, quarter)    
    df_period = filter_by_employment_status(df_period)
    df_period = get_necessary_data(df_period)    
    df_period = employment_and_unemployment_percentage(df_period)    
    return df_period


def filter_by_year_and_quarter(
    df: pd.DataFrame, year: int, quarter: int
    ) -> pd.DataFrame:
    return df[(df["ANO4"] == year) & (df["TRIMESTRE"] == quarter)]


def filter_by_employment_status(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.ESTADO.isin([1, 2])]


def get_necessary_data(df: pd.DataFrame) -> pd.DataFrame:
    # Filtro empleados y desempleados del mismo df (sin agrupar)
    pea = get_agglomerations(df)
    empleados = get_employments(df)
    desempleados = get_unemployments(df)

    # Mergeamos todo
    df_merged = merge_dataframes(pea, empleados)
    df_merged = merge_dataframes(df_merged, desempleados)
    return df_merged
    

def get_agglomerations(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("AGLOMERADO")["PONDERA"].sum().reset_index(name="PEA")


def get_employments(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df[df["ESTADO"] == 1]
        .groupby("AGLOMERADO")["PONDERA"]
        .sum()
        .reset_index(name="OCUPADOS")
    )


def get_unemployments(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df[df["ESTADO"] == 2]
        .groupby("AGLOMERADO")["PONDERA"]
        .sum()
        .reset_index(name="DESOCUPADOS")
    )


def merge_dataframes(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    return pd.merge(df1, df2, on="AGLOMERADO", how="outer").fillna(0)


def employment_and_unemployment_percentage(df: pd.DataFrame) -> pd.DataFrame:
    df["TASA_EMPLEO"] = (df["OCUPADOS"] / df["PEA"] * 100).round(2)
    df["TASA_DESEMPLEO"] = (df["DESOCUPADOS"] / df["PEA"] * 100).round(2)
    return df


def calculate_diff_rate(df_old: pd.DataFrame, df_new: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la variación de las tasas de empleo y desempleo entre dos períodos distintos para cada aglomerado.

    Esta función toma dos DataFrames, correspondientes a dos períodos diferentes (antiguo y reciente),
    y genera un nuevo DataFrame que contiene las tasas originales renombradas, junto con las diferencias
    en tasas de empleo y desempleo.

    Args:
        df_old (pd.DataFrame): DataFrame del período anterior. Debe contener las columnas:
            - "AGLOMERADO"
            - "TASA_EMPLEO"
            - "TASA_DESEMPLEO"
        
        df_new (pd.DataFrame): DataFrame del período más reciente, con las mismas columnas que `df_old`.

    Returns:
        pd.DataFrame: Un nuevo DataFrame con:
            - "AGLOMERADO"
            - "TASA_EMPLEO_OLD", "TASA_DESEMPLEO_OLD"
            - "TASA_EMPLEO_NEW", "TASA_DESEMPLEO_NEW"
            - "DIF_TASA_EMPLEO": Diferencia entre empleo nuevo y viejo
            - "DIF_TASA_DESEMPLEO": Diferencia entre desempleo nuevo y viejo

    """
    df_old_renamed, df_new_renamed = rename_columns(df_old, df_new)
    df_differentiated = merge_for_aglomerate(df_old_renamed, df_new_renamed)
    df_diff_rate = calculated_diff(df_differentiated)
    return df_diff_rate
    
    
def rename_columns(df_old: pd.DataFrame, df_new: pd.DataFrame):
        
        df_old_renamed = df_old[["AGLOMERADO", "TASA_EMPLEO", "TASA_DESEMPLEO"]].rename(
            columns={
                "TASA_EMPLEO": "TASA_EMPLEO_OLD",
                "TASA_DESEMPLEO": "TASA_DESEMPLEO_OLD"
            }
        )

        df_new_renamed = df_new[["AGLOMERADO", "TASA_EMPLEO", "TASA_DESEMPLEO"]].rename(
            columns={
                "TASA_EMPLEO": "TASA_EMPLEO_NEW",
                "TASA_DESEMPLEO": "TASA_DESEMPLEO_NEW"
            }
        )
        
        return df_old_renamed, df_new_renamed

    
def merge_for_aglomerate(df_old: pd.DataFrame, df_new: pd.DataFrame) -> pd.DataFrame:
    return pd.merge(df_old, df_new, on="AGLOMERADO", how="inner")


def calculated_diff(df: pd.DataFrame) -> pd.DataFrame:
    df["DIF_TASA_EMPLEO"] = df["TASA_EMPLEO_NEW"] - df["TASA_EMPLEO_OLD"]
    df["DIF_TASA_DESEMPLEO"] = df["TASA_DESEMPLEO_NEW"] - df["TASA_DESEMPLEO_OLD"]
    return df


def display_map(df: pd.DataFrame, geo_json: dict, tasa_tipo: str) -> folium.Map:
    """
    Genera un mapa interactivo de Argentina con marcadores por aglomerado, donde cada punto
    representa la variación de una tasa (de empleo o desempleo) entre dos momentos del tiempo.

    Args:
        df (pd.DataFrame): DataFrame que contiene los datos de diferencia de tasas por aglomerado.
            Debe incluir las columnas:
                - "AGLOMERADO"
                - "DIF_TASA_EMPLEO"
                - "DIF_TASA_DESEMPLEO"

        geo_json (dict): Diccionario que mapea códigos de aglomerado (como "02", "03") a información
            geográfica, incluyendo:
                - "nombre": Nombre del aglomerado
                - "coordenadas": Lista [latitud, longitud]

        tasa_tipo (str): Tipo de tasa a visualizar. Puede ser:
            - "empleo": Colorea los puntos verde si la tasa de empleo subió, rojo si bajó
            - "desempleo": Verde si la tasa de desempleo bajó, rojo si subió

    Returns:
        folium.Map: Objeto de mapa listo para renderizar en Streamlit mediante `st_folium(...)`.

    Nota:
        Debido a limitaciones del renderizado entre Folium y Streamlit, el color de los íconos (`folium.Icon`) puede no actualizarse visualmente al cambiar el tipo de tasa (`tasa_tipo`),
        aunque los datos y el popup se actualicen correctamente. Este comportamiento no afecta la lógica ni la precisión de los datos mostrados.

    """
    map = generate_map()
    map = clear_markers(map)
    map_with_marker = add_marker(df, geo_json, map, tasa_tipo)
    return map_with_marker
    
    
def generate_map() -> folium.Map:
    map = folium.Map(location=(-38.5, -63), zoom_start=5, control_scale=True)

    folium.TileLayer("OpenStreetMap", name="OSM").add_to(map)

    folium.TileLayer(
        tiles='https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/capabaseargenmap@EPSG%3A3857@png/{z}/{x}/{-y}.png',
        attr="IGN Argentina",
        name="IGN (TMS)",
        overlay=True,
        control=True
    ).add_to(map)
    #el layer control verifica las dos modificaciones posibles de si la pagina llega a estar caida
    folium.LayerControl().add_to(map)

    return map
    
    
def clear_markers(mapa: folium.Map) -> None:
    """
    Elimina únicamente los marcadores (folium.Marker) de un mapa Folium.

    Args:
        mapa (folium.Map): El mapa del que se eliminarán los marcadores.

    Nota:
        Este método modifica el objeto mapa in-place.
    """
    for key, layer in list(mapa._children.items()):
        if isinstance(layer, Marker):
            del mapa._children[key]
    return mapa


def add_marker(
    df_tasas: pd.DataFrame,
    geo_json: dict,
    folium_map: folium.Map,
    tasa_tipo: str
    ) -> folium.Map:
    """
    Agrega marcadores a un mapa de Folium según las diferencias de tasa de empleo o desempleo.

    Recorre cada fila de `df_tasas`, construye el texto del popup y determina
    el color del marcador, y luego lo añade a `folium_map`.

    Args:
        df_tasas (pd.DataFrame): DataFrame con las columnas
            "AGLOMERADO", "DIF_TASA_EMPLEO" y "DIF_TASA_DESEMPLEO".
        geo_json (dict): Diccionario que mapea códigos de aglomerado (por ejemplo "02") a un
            sub-diccionario con las claves:
                - "nombre" (str): nombre del aglomerado
                - "coordenadas" ([lat, lon])
        folium_map (folium.Map): Instancia del mapa Folium donde se añadirán los marcadores.
        tasa_tipo (str): Tipo de tasa a visualizar; puede ser "empleo" o "desempleo".

    Returns:
        folium.Map: La misma instancia de mapa con los marcadores ya agregados.
    """
    for _, row in df_tasas.iterrows():
        try:
            aglo_code = str(int(row["AGLOMERADO"])).zfill(2)
        except (KeyError, ValueError) as exc:
            st.warning(f"No se pudo procesar aglomerado: {exc}")
            continue

        info = geo_json.get(aglo_code)
        if info is None:
            st.warning(f"Aglomerado {aglo_code} no encontrado en geo_json")
            continue

        coords = info["coordenadas"]
        nombre = info["nombre"]
        diff = get_diff(row, tasa_tipo)
        color = get_color(diff, tasa_tipo).lower()
        popup = generate_popup_text(diff, color, nombre, tasa_tipo)

        try:
            folium.Marker(
                location=(coords[0], coords[1]),
                popup=popup,
                icon=folium.Icon(color=color)
            ).add_to(folium_map)
        except Exception as exc:
            st.error(f"Error al agregar marcador para {nombre}: {exc}")

    return folium_map


def get_diff(row, tasa_tipo):
    """
    Obtiene el valor de la diferencia de tasa según el tipo especificado.

    Args:
        row (dict): Un diccionario o objeto que contiene las claves "DIF_TASA_EMPLEO" y "DIF_TASA_DESEMPLEO".
        tasa_tipo (str): El tipo de tasa, puede ser "empleo" o "desempleo".

    Returns:
        float or None: El valor de la diferencia de tasa correspondiente, o None si el tipo no es reconocido.
    """
    diff = None
    if tasa_tipo == "empleo":
        diff = row["DIF_TASA_EMPLEO"]
    elif tasa_tipo == "desempleo":
        diff = row["DIF_TASA_DESEMPLEO"]
    return diff


def generate_popup_text(diff: float, color: str, nombre: str, tasa_tipo: str) -> str:
    """
    Genera el texto del popup para el marcador.

    Args:
        nombre (str): El nombre del aglomerado.

        tasa_tipo (str): El tipo de tasa, puede ser "empleo" o "desempleo".

    Returns:
        str: El texto formateado para el popup.
    """
    return (
        f"<b>{nombre}</b><br>"
        f"Diferencia en tasa de {tasa_tipo}: "
        f"<span style='color:{color}'>{diff:+.2f}%</span>"
    )


def get_color(diff: float, tasa_tipo: str) -> str:
    """
    Devuelve el color del ícono según la diferencia y el tipo de tasa.

    Args:
        diff (float): Valor de la diferencia de tasa.
        tasa_tipo (str): "empleo" o "desempleo".

    Returns:
        str: "green", "red" o "blue" (default).
    """
    if tasa_tipo == "empleo":
        return "green" if diff > 0 else "red"
    if tasa_tipo == "desempleo":
        return "green" if diff > 0 else "red"
    return "blue"

if (__name__ == "__main__"):

    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
    data_path = Path("merge") / "merge_individual.csv"
    df = pd.read_csv(data_path,encoding="utf-8",sep=";")
    
    st.divider()
    st.subheader("Mapeo de tasa de empleo y desempleo por algomerado")
    
    dict_trim = {"2024" : 1, 
                 "2022" : 1}
    
    tasa_tipo = st.selectbox(
            "Seleccione el tipo de tasa a mostrar en el mapa",
            options=["empleo", "desempleo"]
        )
    
    #tasa_tipo = "desempleo"
    
    mapa = get_map_employment_unemployment_variation_by_agglomerate(df, dict_trim, tasa_tipo)

    st.header("Mapa de aglomerados segun su taza", divider="red")
    
    st_folium(mapa, key=f"map_{tasa_tipo}", width=700, height=500)
    
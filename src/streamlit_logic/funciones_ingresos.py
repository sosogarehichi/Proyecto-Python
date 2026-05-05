import os
import sys
from pathlib import Path
import pandas as pd
import streamlit as st


def trim_map(trimestre):
    """
    Devuelve una lista de los nombres de los meses correspondientes
    a un trimestre.
    """
    map = {
        1: ["enero", "febrero", "marzo"],
        2: ["abril", "mayo", "junio"],
        3: ["julio", "agosto", "septiembre"],
        4: ["octubre", "noviembre", "diciembre"]
    }
    return map.get(int(trimestre), [])


def get_df_canasta():
    def get_canasta_path():
        code_path = Path(__file__).parent.parent.parent
        data_path = code_path / "data"
        canasta_path = data_path / "valores-canasta-basica-alimentos-canasta-basica-total-mensual-2016.csv"
        return canasta_path

    canasta_path = get_canasta_path()
    df_canasta = pd.read_csv(canasta_path, delimiter=",", encoding="utf-8")
    return df_canasta


def hogares_aptos_filtrados(df: pd.DataFrame, year: int, trimester: int, integrantes: int = 4) -> pd.DataFrame:
    """
    Filtra y prepara el DataFrame de hogares de la EPH para el análisis contra la canasta básica.

    Esta función aplica los siguientes pasos:
    1. Filtra el DataFrame según el año, trimestre y cantidad de integrantes especificados.
    2. Excluye hogares cuyo ingreso total familiar (ITF) sea menor o igual a cero.
    3. Devuelve un único registro por hogar, con columnas clave para el análisis económico.

    Muestra una advertencia (vía Streamlit) con la cantidad de hogares excluidos por ingreso inválido.

    Parameters:
        df (pd.DataFrame): DataFrame original con registros individuales de personas del EPH.
        year (int): Año a filtrar.
        trimester (int): Trimestre a filtrar (1 a 4).
        integrantes (int, optional): Número exacto de integrantes del hogar (por defecto 4).

    Returns:
        pd.DataFrame: DataFrame con un hogar por fila, incluyendo ingreso total, PONDERA e IX_TOT.
    """
    df_filtrado = filtrar(df, year, trimester,integrantes)
    df_hogares = hogares_unicos(df_filtrado)
    return df_hogares


def filtrar(df: pd.DataFrame, year: int, trimester: int, integrantes: int) -> pd.DataFrame:
    """
    Filtra un DataFrame de hogares de la EPH para obtener únicamente aquellos correspondientes
    al año y trimestre especificados, que además tengan exactamente 4 integrantes y un ingreso
    total familiar (ITF) mayor a cero.

    Esta función interna utiliza pandas.query para aplicar múltiples filtros de forma legible 
    y eficiente. También informa la cantidad de hogares excluidos por no tener ingresos válidos.

    Args:
        df (pd.DataFrame): DataFrame original con datos de la Encuesta Permanente de Hogares.
        year (int): Año a filtrar (por ejemplo, 2023).
        trimester (int): Trimestre a filtrar (valor entre 1 y 4).

    Returns:
        pd.DataFrame: DataFrame filtrado con hogares de 4 integrantes y datos válidos 
                    pertenecientes al período especificado.
    """
    def filtrar_hogares(df: pd.DataFrame, year: int, trimester: int, integrantes: int ) -> pd.DataFrame:
        """
        Aplica un filtrado específico al DataFrame para extraer hogares del año y trimestre indicados,
        con un número exacto de integrantes y un ingreso total familiar mayor a cero.

        Args:
            df (pd.DataFrame): DataFrame con registros de hogares.
            year (int): Año a analizar.
            trimester (int): Trimestre dentro del año (del 1 al 4).
            integrantes (int): Número exacto de integrantes que debe tener el hogar.

        Returns:
            pd.DataFrame: Subconjunto del DataFrame con los hogares filtrados según los criterios dados.
        """
        # Filtrar por año, trimestre, hogares de 4 personas y con ingreso familiar válido (> 0)
        return df.query("ANO4 == @year and TRIMESTRE == @trimester and IX_TOT == @integrantes and ITF > 0").copy()

    n_excluidos = df["ITF"].le(0).sum()
    st.warning(f"{n_excluidos} hogares fueron excluidos por no tener un ingreso familiar declarado válido.")
    return filtrar_hogares(df, year, trimester, integrantes)


def hogares_unicos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ddevuelve un único registro por hogar con las columnas necesarias para análisis socioeconómico,
    incluyendo el cálculo del coeficiente de equivalencia ajustado por composición etaria.

    Elimina duplicados por hogar (usando CODUSU y NRO_HOGAR) y conserva variables clave: 
    ingreso total familiar (renombrado como 'ingreso_total'), ponderador (PONDERA), total de integrantes, 
    cantidad de menores de 10 años y mayores o iguales a 10, y una columna adicional 'equivalencia' que 
    representa el consumo equivalente del hogar.

    La equivalencia se calcula asignando:
        - 1.0 al primer adulto
        - 0.5 a

    Parameters:
        df (pd.DataFrame): DataFrame de personas con columnas de identificación y atributos del hogar.

    Returns:
        pd.DataFrame: Un registro por hogar, con columnas relevantes para análisis económico.
    """
    columnas = [
        "CODUSU", "NRO_HOGAR", "ITF", "PONDERA", "IX_TOT", "IX_MEN10", "IX_MAYEQ10"
    ]
    hogares = df.drop_duplicates(subset=["CODUSU", "NRO_HOGAR"])[columnas].copy()
    hogares.rename(columns={"ITF": "ingreso_total"}, inplace=True)

    # Calcular equivalencia según estructura: 1 adulto + resto adultos como 0.5 + menores como 0.3
    hogares["equivalencia"] = (
        1 + (hogares["IX_MAYEQ10"] - 1) * 0.5 + hogares["IX_MEN10"] * 0.3
    )
    return hogares


def consolidar_canasta_por_trimestre(canasta_df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa el dataset mensual de la canasta básica por año y trimestre,
    y calcula el promedio trimestral de línea de indigencia y pobreza.

    Parameters:
        canasta_df (pd.DataFrame): DataFrame con columnas 'indice_tiempo', 'linea_indigencia', 'linea_pobreza'

    Returns:
        pd.DataFrame: DataFrame agrupado con columnas 'año', 'trimestre', 'cba_prom', 'cbt_prom'
    """
    canasta_df = canasta_df.copy()
    canasta_df = identificar_trimestre(canasta_df)    
    df_canasta_final = agrupar_por_año_y_trimestre(canasta_df)    
    return df_canasta_final


def identificar_trimestre(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrae y agrega al DataFrame las columnas 'año', 'mes' y 'trimestre' a partir de 'indice_tiempo'.

    Esta función convierte la columna 'indice_tiempo' a tipo datetime (si no lo está),
    y calcula el trimestre del año correspondiente a cada registro según el mes.

    Parameters:
        df (pd.DataFrame): DataFrame que contiene al menos una columna 'indice_tiempo' con fechas mensuales.

    Returns:
        pd.DataFrame: El mismo DataFrame con las nuevas columnas 'año', 'mes' y 'trimestre' agregadas.
    """
    df["indice_tiempo"] = pd.to_datetime(df["indice_tiempo"])
    df["año"] = df["indice_tiempo"].dt.year
    df["mes"] = df["indice_tiempo"].dt.month
    df["trimestre"] = ((df["mes"] - 1) // 3) + 1
    return df


def agrupar_por_año_y_trimestre(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa los datos por año y trimestre y calcula los valores promedio trimestrales
    de la línea de indigencia y la línea de pobreza.

    Asume que el DataFrame tiene las columnas 'año', 'trimestre', 'linea_indigencia' y 'linea_pobreza'.

    Parameters:
        df (pd.DataFrame): DataFrame con valores mensuales de la canasta ya enriquecido con las columnas
                        'año' y 'trimestre'.

    Returns:
        pd.DataFrame: DataFrame agrupado con una fila por combinación de año y trimestre,
                    incluyendo columnas 'cba_prom' (promedio línea de indigencia) y
                    'cbt_prom' (promedio línea de pobreza).
    """
    agrupado = df.groupby(["año", "trimestre"]).agg(
        cba_prom=("linea_indigencia", "mean"),
        cbt_prom=("linea_pobreza", "mean")
    ).reset_index()
    return agrupado


def complementar_datos(df_hogares: pd.DataFrame, df_canasta: pd.DataFrame, year: int, trimester: int) -> pd.DataFrame:
    """
    Integra los datos de hogares con los valores promedio de la canasta básica para un trimestre determinado,
    ajusta los umbrales de pobreza e indigencia según la equivalencia de cada hogar, y clasifica su condición económica.

    Parameters:
        df_hogares (pd.DataFrame): DataFrame con hogares únicos, incluyendo ingreso_total y equivalencia.
        df_canasta (pd.DataFrame): DataFrame con valores promedios de canasta por año y trimestre (cba_prom, cbt_prom).
        year (int): Año de análisis.
        trimester (int): Trimestre de análisis (1 a 4).

    Returns:
        pd.DataFrame: DataFrame con columnas nuevas: umbrales ajustados y condición socioeconómica.
    """
    def merge_data(df_hogares: pd.DataFrame, df_canasta: pd.DataFrame) -> pd.DataFrame:        
        return df_hogares.merge(
            df_canasta, on=["año", "trimestre"], how="left"
        )
    
    df_completo = df_hogares.copy()
    df_completo["año"] = year
    df_completo["trimestre"] = trimester
    df_completo = merge_data(df_completo, df_canasta)
    df_completo = traer_umbrales_ajustados(df_completo)
    df_completo = establecer_condicion(df_completo)
    return df_completo


def traer_umbrales_ajustados(df_hogares: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula los umbrales de indigencia y pobreza personalizados para cada hogar,
    multiplicando la equivalencia por los valores promedio trimestrales.

    Parameters:
        df_hogares (pd.DataFrame): DataFrame con equivalencia y valores de canasta por hogar.

    Returns:
        pd.DataFrame: DataFrame con columnas nuevas: 'umbral_indigencia_ajustado' y 'umbral_pobreza_ajustado'.
    """
    df_hogares["umbral_indigencia_ajustado"] = (
        df_hogares["equivalencia"] * df_hogares["cba_prom"]
    )
    df_hogares["umbral_pobreza_ajustado"] = (
        df_hogares["equivalencia"] * df_hogares["cbt_prom"]
    )
    return df_hogares


def establecer_condicion(df_hogares: pd.DataFrame) -> pd.DataFrame:
    """
    Clasifica cada hogar en una de tres condiciones económicas:
    - 'indigente': si el ingreso total está por debajo del umbral de indigencia ajustado
    - 'pobre': si está entre el umbral de indigencia y el de pobreza
    - 'no pobre': si supera el umbral de pobreza ajustado

    Parameters:
        df_hogares (pd.DataFrame): DataFrame con ingresos y umbrales ajustados por hogar.

    Returns:
        pd.DataFrame: Mismo DataFrame con una nueva columna 'condicion'.
    """
    def clasificar_hogar(row: pd.Series) -> str:
        if row["ingreso_total"] < row["umbral_indigencia_ajustado"]:
            return "indigente"
        elif row["ingreso_total"] < row["umbral_pobreza_ajustado"]:
            return "pobre"
        else:
            return "no pobre"

    df_hogares["condicion"] = df_hogares.apply(clasificar_hogar, axis=1)
    return df_hogares


def resumen_ponderado_por_condicion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resume el total de hogares y porcentaje ponderado por condición socioeconómica
    ('indigente', 'pobre', 'no pobre') usando la variable de expansión PONDERA.

    Parameters:
        df (pd.DataFrame): DataFrame con columna 'condicion' y 'PONDERA'.

    Returns:
        pd.DataFrame: DataFrame con columnas 'condicion', 'hogares_ponderados' y '%_ponderado'.
    """
    resumen = agrupar_por_condicion_socioeconomica(df)
    resumen = porcentaje_de_cada_grupo(resumen)

    return resumen.sort_values("condicion")


def agrupar_por_condicion_socioeconomica(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa el DataFrame por la columna 'condicion' y suma los valores de 'PONDERA'.

    Parameters:
        df (pd.DataFrame): DataFrame con columna 'condicion' y 'PONDERA'.

    Returns:
        pd.DataFrame: DataFrame agrupado con la suma de 'PONDERA' por cada condición.
    """
    return df.groupby("condicion", as_index=False).agg(
        hogares_ponderados=("PONDERA", "sum")
    )

def porcentaje_de_cada_grupo(resumen: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el porcentaje ponderado de cada grupo respecto al total de hogares ponderados.

    Parameters:
        resumen (pd.DataFrame): DataFrame con la suma de 'PONDERA' por condición.

    Returns:
        pd.DataFrame: DataFrame con una nueva columna '%_ponderado'.
    """
    total = resumen["hogares_ponderados"].sum()
    resumen["porcentaje_ponderado"] = (resumen["hogares_ponderados"] / total * 100).round(2)
    return resumen


def obtener_datos_completos_de_hogares_con_canasta_basica(df_merge_hogar: pd.DataFrame, year: int, trimester:int):
    """
    Ejecuta el proceso completo para analizar hogares según criterios socioeconómicos,
    integrando ingresos, estructura familiar y umbrales de pobreza e indigencia.

    Este pipeline:
    - Filtra hogares según período y estructura válida.
    - Obtiene y promedia los valores de la canasta básica por trimestre.
    - Une los datos de hogares y canasta por periodo.
    - Calcula los umbrales ajustados por equivalencia y clasifica cada hogar.

    Parameters:
        df_merge_hogar (pd.DataFrame): DataFrame con registros de hogares individuales con estructura e ingresos.
        year (int): Año de referencia para el análisis.
        trimester (int): Trimestre del año (1 a 4).

    Returns:
        pd.DataFrame: DataFrame con un hogar por fila, incluyendo clasificación socioeconómica y métricas ajustadas.
    """
    df_filtrado = hogares_aptos_filtrados(df_merge_hogar, year, trimester)
    df_canasta = get_df_canasta()
    df_canasta_promediada = consolidar_canasta_por_trimestre(df_canasta)
    df_completo = complementar_datos(
        df_filtrado, df_canasta_promediada, year, trimester
    )
    return df_completo


def calcular_pobreza_e_indigencia(df_merge_hogar: pd.DataFrame, year: int, trimester: int, solicitar_df: bool = False) -> pd.DataFrame:
    """
    Calcula un resumen ponderado de hogares clasificados por condición socioeconómica (indigente, pobre, no pobre),
    y opcionalmente devuelve el DataFrame completo con cada hogar clasificado.

    Parameters:
        df_merge_hogar (pd.DataFrame): Dataset de hogares con ingresos, estructura, equivalencia, etc.
        year (int): Año de análisis.
        trimester (int): Trimestre del año (1 a 4) a evaluar.
        solicitar_df (bool, optional): Si es True, retorna solo el resumen; si es False (por defecto),
                                       retorna también el DataFrame completo.

    Returns:
        pd.DataFrame or tuple:
            - Si solicitar_df=True: DataFrame resumen con totales y porcentajes ponderados por condición.
            - Si solicitar_df=False: (resumen, df_completo)
    """
    df_completo = obtener_datos_completos_de_hogares_con_canasta_basica(
        df_merge_hogar, year, trimester
    )
    resumen = resumen_ponderado_por_condicion(df_completo)
    if solicitar_df:
        return resumen
    else:
        return resumen, df_completo


if (__name__ == "__main__"):
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    import src.utils as utils
    df_merge_hogar = utils.cargar_merge("hogar")          
    dict_trim = st.session_state.get("dict_trim", {})

    st.title("Ingresos 💰")

    year = st.selectbox(
        "Seleccione el año:",
        dict_trim.keys(),
        key="mi_selectbox_year_unico"
    )
    year = int(year)  # Convertir a entero para evitar problemas de tipo

    trimester = st.selectbox(
        "Seleccione el trimestre:",
        df_merge_hogar[(df_merge_hogar["ANO4"] == year)]["TRIMESTRE"].unique(),
        key="mi_selectbox_trimestre_unico")

    df_completo = obtener_datos_completos_de_hogares_con_canasta_basica(
        df_merge_hogar, year, trimester
    )
    st.write("Datos completos de hogares con canasta básica:")
    st.write(df_completo)

    resumen = resumen_ponderado_por_condicion(df_completo)
    st.write("Resumen ponderado por condición socioeconómica:")
    st.write(resumen)

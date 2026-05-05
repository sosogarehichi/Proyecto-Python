from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
import src.streamlit_logic.funciones_caracteristicas_demograficas as utils
import src.streamlit_logic.funciones_caracteristicas_demograficas as utilities
from src.procesamiento_individual import \
    get_top5_agglomerates_by_educated_households
import pandas as pd
import streamlit as st


def get_population_by_education_level(df: pd.DataFrame, year: int):
    """
    Devuelve la cantidad de personas según el nivel educativo
    alcanzado para un año específico.

    Parámetros:
        df (pd.DataFrame): DataFrame individual con la columna 'ANO4' y
        'NIVEL_ED_str'.
        year (int): Año seleccionado por el usuario.

    Retorna:
        pd.DataFrame: DataFrame con dos columnas: 'Nivel educativo' y
        'Cantidad de personas'.
    """
    # Filtrar por año
    df_year = df[df["ANO4"] == year]

    if df_year.empty:
        return pd.DataFrame(columns=["Nivel educativo", "Cantidad de personas"])

    # Agrupar por nivel educativo y contar
    result = (
        df_year["NIVEL_ED_str"]
        .value_counts()
        .rename_axis("Nivel educativo")
        .reset_index(name="Cantidad de personas")
        .sort_values("Cantidad de personas", ascending=False)
    )

    return result


def years(df):
    # Creo un listado con los años disponibles en el DataFrame
    years = df['ANO4'].unique().tolist()
    # Ordeno los años
    years.sort()
    return years


def alfabetismo(df):
    """
    Muestra, para cada año el porcentaje de personas
    mayores de 6 años que saben y no saben leer y escribir.
    Args: 
        df (DataFrame): DataFrame con los datos de los individuos.
    """
    # Verifico que existan las columnas necesarias
    if 'ANO4' not in df.columns or 'CH06' not in df.columns or 'CH09' not in df.columns or 'PONDERA' not in df.columns:
        st.error("❌ No se encontraron las columnas necesarias en el archivo.")
        return

    # Listado de años del dataframe
    list_years = years(df)

    # Creo los tabs para cada año de la lista
    tabs = st.tabs([f"Año {a}" for a in list_years])

    # Recorro cada año junto con su tab
    for year, tab in zip(list_years, tabs):
        with tab:
            st.subheader(f" Alfabetismo - Año {int(year)}")

            # Preparo los datos y calculos los porcentajes
            all, literate, illiterate, pct_illiterate, pct_literate = data(
                df, year)

            # Muestro los resultados
            st.markdown(f"""
                - 👥 Total personas mayores de 6 años con datos válidos: {all} 
                - 📘 Saben leer y escribir: {literate} ({pct_literate:.2f}%)
                - ❌ No saben leer y escribir: {illiterate} ({pct_illiterate:.2f}%)
            """)

            # Muestro el grafico de barras
            st.bar_chart({
                "Alfabetismo": [pct_literate, pct_illiterate]
            }, use_container_width=True)


def data(df, year):
    """
    Filtra y calcula las estadísticas de alfabetismo para personas mayores de
    6 años en un año específico.
    Args:
        df (DataFrame): DataFrame con los datos individuales, incluyendo las
        columnas 'ANO4', 'CH06', 'CH09' y 'PONDERA'.
        year
    Returns:
        all (int): Total de personas mayores de 6 años con datos válidos
        de alfabetismo (sin ponderar).
        literate (int): Cantidad de personas que saben leer y
        escribir (sin ponderar).
        illiterate (int): Cantidad de personas que no saben leer y
        escribir (sin ponderar).
        pct_illiterate (float): Porcentaje ponderado de personas
        no alfabetizadas.
        pct_literate (float): Porcentaje ponderado de personas alfabetizadas.
    """
    # Filtro solo por el año y las personas mayores a 6 años correspondientes
    # al tad actual
    df_year = df[(df['ANO4'] == year) & (df['CH06'] > 6)]

    # Filtro por si sabe o no leer y descarto el 3, 1 = sabe, 2 = no sabe
    df_filtered = df_year[df_year['CH09'] <= 2]

    pondera = df_filtered['PONDERA'].sum()

    # cantidad total
    all = len(df_filtered)
    # Cantidad de personas que saben leer y escribir
    literate = (df_filtered['CH09'] == 1).sum()
    # Cantidad de personas que no saben leer y escribir
    illiterate = (df_filtered['CH09'] == 2).sum()

    # Suma ponderada personas que saben leer y escribir
    literate_ponderado = df_filtered.loc[df_filtered['CH09'] == 1, 'PONDERA'].sum(
    )
    # Suma ponderada personas que no saben leer y escribir
    illiterate_ponderado = df_filtered.loc[df_filtered['CH09'] == 2, 'PONDERA'].sum(
    )

    # Calculo los porcentajes
    pct_literate = (literate_ponderado / pondera) * 100
    pct_illiterate = (illiterate_ponderado / pondera) * 100

    return all, literate, illiterate, pct_illiterate, pct_literate


def show_top5_agglomerates_by_educated_households(df):
    """
    Muestra los 5 aglomerados con mayor porcentaje de hogares con
    2 o más integrantes con estudios universitarios o superiores
    alcanzados.
    """
    top5 = get_top5_agglomerates_by_educated_households(df)
    # top5 es una Serie con índice = aglomerado y valores = porcentaje
    top5_df = top5.reset_index()  # Convierte el índice en columna
    top5_df.columns = ['Aglomerado', 'Porcentaje']  # Renombra las columnas
    return top5_df


def analyze_education_by_age_group(df: pd.DataFrame) -> pd.Series:
    """
    Determina el nivel educativo más frecuente por grupo etario a partir de un
    DataFrame de personas encuestadas.

    Esta función agrega una columna 'RANGO_ETARIO' según la edad de cada
    individuo (columna 'CH06'), clasificándolos
    en tramos definidos. Luego, agrupa los datos por rango etario y calcula la
    moda (nivel educativo más común)
    en la columna 'NIVEL_ED_str'. En caso de empate, se selecciona
    arbitrariamente el primer valor.

    Args:
        df (pd.DataFrame): DataFrame con al menos las siguientes columnas:
            - 'CH06': Edad de la persona
            - 'NIVEL_ED_str': Nivel educativo expresado como texto

    Returns:
        pd.Series: Serie indexada por 'RANGO_ETARIO', con el nivel educativo más frecuente por grupo.
    """

    def create_age_group_column(df_input: pd.DataFrame) -> pd.DataFrame:

        def classify_age_range(age) -> str:
            if pd.isnull(age):
                return "sin dato"
            elif 20 <= age < 30:
                return "20-29"
            elif 30 <= age < 40:
                return "30-39"
            elif 40 <= age < 50:
                return "40-49"
            elif 50 <= age < 60:
                return "50-59"
            elif age >= 60:
                return "60+"
            else:
                return "menor de 20"

        df_output = df_input.copy()
        df_output["RANGO_ETARIO"] = df_output.apply(lambda row: classify_age_range(row["CH06"]), axis=1) 
        return df_output

    def get_modal_education_by_age_range(df: pd.DataFrame) -> pd.Series:
        """
        Calcula el nivel educativo más frecuente (moda) dentro de cada
        grupo etario.

        Agrupa el DataFrame por la columna 'rango_etario' y determina,
        para cada grupo, cuál es el valor más común de la columna
        'NIVEL_ED_str'. En caso de empate, devuelve uno arbitrariamente
        (el primero).

        Args:
            df (pd.DataFrame): DataFrame que contiene las columnas:
                - 'rango_etario': categorización etaria por tramo
                - 'NIVEL_ED_str': nivel educativo expresado como texto

        Returns:
            pd.Series: Serie indexada por rango etario, con el nivel educativo
            más frecuente por grupo.
        """
        return df.groupby("RANGO_ETARIO")["NIVEL_ED_str"].agg(lambda x: x.mode().iloc[0])

    df_with_age_group = create_age_group_column(df)
    modal_education_by_age_range = get_modal_education_by_age_range(df_with_age_group)

    return modal_education_by_age_range


if (__name__ == "__main__"):
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
    data_path = Path("merge") / "merge_individual.csv"
    df = pd.read_csv(data_path, encoding="utf-8", sep=";")

    modal_education = analyze_education_by_age_group(df)        

    print(modal_education)

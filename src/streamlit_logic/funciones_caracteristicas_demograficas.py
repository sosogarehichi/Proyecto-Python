
import pandas as pd
from pathlib import Path
from src.procesamiento_hogar import translate_aglom
import matplotlib.pyplot as plt
import sys


def calculate_dependency_evolution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la evolución de la dependencia demográfica por año y trimestre para cada aglomerado.

    Parámetros:
        df (pd.DataFrame): DataFrame con columnas AGLOMERADO, ANO4, TRIMESTRE, CH06.

    Retorna:
        pd.DataFrame: DataFrame con la tasa de dependencia por aglomerado (nombre), año y trimestre.
    """

    def classify_age_group(age: int):
        if age <= 14:
            return "dependiente"
        elif age <= 64:
            return "activa"
        else:
            return "dependiente"

    df = df.copy()
    df["grupo_edad"] = df["CH06"].apply(classify_age_group)

    grouped = (
        df.groupby(["AGLOMERADO", "ANO4", "TRIMESTRE", "grupo_edad"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    grouped["Tasa de dependencia"] = (
        grouped["dependiente"] / grouped["activa"] * 100
    ).round().astype(int)

    # Renombrar ANO4 → Año
    grouped = grouped.rename(columns={"ANO4": "Año"})

    # Traduce los códigos de los aglomerados
    grouped["Aglomerado"] = grouped["AGLOMERADO"].apply(translate_aglom)

    # Reordena columnas dejando "Aglomerado" primero
    result = grouped[["Aglomerado", "Año", "TRIMESTRE", "Tasa de dependencia"]]

    return result


def give_grafic_distribution_age_gender(df: pd.DataFrame, year:int, trimester:int):
    """
    Genera un gráfico de barras que muestra la distribución de la población por edad y sexo.

    Parámetros:
        df (pd.DataFrame): DataFrame con columnas ANO4, TRIMESTRE, CH04_str, CH06.
        year (int): Año para filtrar los datos.
        trimester (int): Trimestre para filtrar los datos.

    Retorna:
        matplotlib.figure.Figure: Figura del gráfico generado.
    """
    distribution = give_distribution_age_gender(df, year, trimester)
    grafic = give_grafic(distribution)
    return grafic


def give_grafic(distribution: pd.DataFrame) -> plt.Figure:
    
    pivot_df = distribution.pivot_table(index="grupo_edad", columns="CH04_str", values="conteo", fill_value=0)

    orden_grupos = ["0-9", "10-19", "20-29", "30-39", "40-49", 
                    "50-59", "60-69", "70-79", "80-89", "90+"]

    pivot_df = pivot_df.reindex(orden_grupos).fillna(0)

    fig, ax = plt.subplots()

    x = range(len(pivot_df.index))
    ancho = 0.4

    masculino = pivot_df.get("Masculino", pd.Series([0]*len(x)))
    femenino = pivot_df.get("Femenino", pd.Series([0]*len(x)))

    ax.bar([i - ancho/2 for i in x], masculino, width=ancho, label="Masculino")
    ax.bar([i + ancho/2 for i in x], femenino, width=ancho, label="Femenino")

    ax.set_xlabel("Grupos de edad")
    ax.set_ylabel("Población")
    ax.set_title("Distribución por edad y sexo")
    ax.set_xticks(x)
    ax.set_xticklabels(pivot_df.index, rotation=45)
    ax.legend()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))

    return fig

def give_distribution_age_gender(df,year,trimester):

    df_filtrado = df[(df.ANO4 == year) & (df.TRIMESTRE == trimester)]

    # falta grupar edades en intervalos de 10 años
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    labels = ['0-9', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90+']

    df_filtrado["grupo_edad"] = pd.cut(df_filtrado.CH06, bins=bins, labels=labels, right=False)
    
    distribucion = df_filtrado.groupby(["grupo_edad","CH04_str"]).PONDERA.sum().reset_index(name="conteo")
        
    return  distribucion

    
def get_avg_age_by_agglomerate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la edad promedio por aglomerado para el año y trimestre más recientes.

    Retorna:
        pd.DataFrame: DataFrame con columnas 'aglomerado' y 'Edad promedio'.
    """
    # Obtener el último año y trimestre disponibles
    max_year = df["ANO4"].max()
    max_trim = df[df["ANO4"] == max_year]["TRIMESTRE"].max()

    # Filtrar el DataFrame por ese período
    df_filtered = df[(df["ANO4"] == max_year) & (df["TRIMESTRE"] == max_trim)]

    # Agrupar por aglomerado y calcular la edad promedio
    result = (
        df_filtered
        .groupby("AGLOMERADO", as_index=False)["CH06"]
        .mean()
        .rename(columns={"CH06": "Edad promedio"})
    )

    # Traducir códigos de aglomerado a nombres legibles
    result["aglomerado"] = result["AGLOMERADO"].apply(translate_aglom)

    # Conservar solo las columnas deseadas
    result = result[["aglomerado", "Edad promedio"]]

    return result


def get_age_stats_by_year_trim(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la media y mediana de la edad por año y trimestre.

    Parámetros:
        df (pd.DataFrame): DataFrame con columnas ANO4, TRIMESTRE, CH06.

    Retorna:
        pd.DataFrame: DataFrame con columnas ANO4, TRIMESTRE, Edad_media y Edad_mediana.
    """
    result = (
        df.groupby(["ANO4", "TRIMESTRE"], as_index=False)["CH06"]
        .agg(Edad_media="mean", Edad_mediana="median")
        
    )

    result["Edad_media"] = result["Edad_media"].round(0).astype(int)
    result["Edad_mediana"] = result["Edad_mediana"].round(0).astype(int)


    return result
    
    
if (__name__ == "__main__"):
    
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
    data_path = Path("merge") / "merge_individual.csv"
    df = pd.read_csv(data_path,encoding="utf-8",sep=";")
    year = 2024
    trimester = 1

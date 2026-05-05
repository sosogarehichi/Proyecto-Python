import pandas as pd
import streamlit as st
import numpy as np
import json
from src.procesamiento_hogar import translate_aglom
from pathlib import Path
import matplotlib.pyplot as plt
import sys
import plotly.express as px

def get_total_viviendas_por_anio(df_hogar):
    """
    Retorna la cantidad total de viviendas (hogares únicos) encuestadas para un año determinado.
    Solo se consideran aquellas donde la encuesta fue realizada (REALIZADA == 1).
    """
    # Filtrar por año y encuestas realizadas
    df_filtrado = df_hogar[
         (df_hogar["REALIZADA"] == 1)
    ]

    # Eliminar duplicados por CODUSU y NRO_HOGAR
    viviendas_unicas = df_filtrado.drop_duplicates(subset=["CODUSU", "NRO_HOGAR"])

    # Retornar cantidad total
    return len(viviendas_unicas)


def income(df):
    """Retorna un año seleccionado por el usuario."""
    aglom_ids = df['AGLOMERADO'].unique().tolist()
    aglom_ids.sort()
    aglom_options = {}
    # Traducimos los IDs de aglomerados a los nombres correspondientes
    for aglo_id in aglom_ids:
        name_aglom = translate_aglom(aglo_id)
        if name_aglom:  # si se puede traducir
            aglom_options[name_aglom] = aglo_id
    return aglom_options 


def proportion_bathroom(df):
    """Muestra los calculos de la proporcion de viviendas con baño por aglomerado y año."""
    # Verificar que las columnas necesarias existan
    if 'IV9' not in df.columns or 'AGLOMERADO' not in df.columns or 'PONDERA' not in df.columns:
        st.error("❌ No se encontraron las columnas necesarias en el archivo.")
        return

    data = proportions(df)

    # Mostrar tabla con porcentajes
    # st.dataframe(data[['Aglomerado', 'proporcion_str']].rename(columns={'proporcion_str': 'Proporción con baño'}))
    # Mostrar gráfico con valores numéricos reales
    st.bar_chart(data.set_index('Aglomerado')['proporcion'])


def proportions(df):
    """ Genera un resumen de las proporciones de las viviendas con baño por aglomerado.
    Args: 
        df (DataFrame): DataFrame con los datos de las viviendas.
    Returns: 
        data (DataFrame): DataFrame con la proporcion de viviendas con baño por aglomerado."""
    # Filtrar viviendas con baño (IV9 == 1)
    df_bathroom = df[df['IV9'] == 1]
    # Agrupar por aglomerado: total de viviendas
    data = df.groupby('AGLOMERADO').agg(total_viviendas=('PONDERA', 'sum'))
    # Agregar la cantidad de viviendas con baño
    data['con_bano'] = df_bathroom.groupby('AGLOMERADO')['PONDERA'].sum()
    # Reemplazar los valores nulos por 0 (aglomerados sin viviendas con baño)
    data['con_bano'] = data['con_bano'].fillna(0)
    # Calcular la proporción (como número decimal)
    data['proporcion'] = data['con_bano'] / data['total_viviendas']
    # Crear columna con porcentaje como texto formateado (ej: '85.71%')
    data['proporcion_str'] = data['proporcion'].apply(lambda x: f"{x * 100:.2f}%")
    # Traducir los códigos de aglomerado a nombres
    data['Aglomerado'] = data.index.map(translate_aglom)
    # Eliminar filas sin nombre traducido
    data = data[data['Aglomerado'].notna()]
    # Ordenar por mayor proporción
    data = data.sort_values(by='proporcion', ascending=False)
    return data


def translate_tenure(value):
    """Traduce el valor del régimen de tenencia a su descripción.
    Args:
        value: valor del régimen de tenencia.
    Returns:
        str: descripción del régimen de tenencia
    """
    tenure_regime = {
        1: 'Propietario de la vivienda y el terreno',
        2: 'Propietario de la vivienda solamente',
        3: 'Inquilino / arrendatario de la vivienda',
        4: 'Ocupante por pago de impuestos / expensas',
        5: 'Ocupante en relación de dependencia',
        6: 'Ocupante gratuito (con permiso)',
        7: 'Ocupante de hecho (sin permiso)',
        8: 'Está en sucesión'
    }
    try:
        return tenure_regime.get(int(value))
    except (ValueError, TypeError):
        return None


def select_tenure(df, agglomerate_id):
    """Selecciona la dependencia de la vivienda por aglomerado y año.
    Args:
        df (DataFrame): DataFrame con los datos de las viviendas.
        agglomerate_id: ID del aglomerado seleccionado por el usuario.
    Returns:
        tenure_options: diccionario con las opciones del regimen de tenencia"""

    df = df[df['AGLOMERADO'] == agglomerate_id]
    tenure = df['II7'].dropna().unique().tolist()
    tenure.sort()
    tenure_options = {}
    for ten_id in tenure:
        type_tenure = translate_tenure(ten_id)
        if type_tenure:
            tenure_options[type_tenure] = ten_id
    return tenure_options


def tenure_regime_evolution(df, agglomerate_id, selected_tenures):

    # Filtrar por aglomerado
    df = df[df['AGLOMERADO'] == agglomerate_id]

    # Obtener opciones de tenencia disponibles para ese aglomerado
    tenure_options = select_tenure(df, agglomerate_id)

    # Construir diccionario invertido código -> nombre, verificando duplicados
    name_to_code = tenure_options
    code_to_name = {}
    # Recorremos cada par nombre, código en el diccionario original
    for nombre, codigo in name_to_code.items():
        # Validamos que el código sea único para evitar sobreescrituras accidentales
        if codigo in code_to_name:
            st.warning(f"Advertencia: código {codigo} duplicado para '{nombre}' y '{code_to_name[codigo]}'. Se mantiene el primero.")
        else:
            # Insertamos en el diccionario invertido
            code_to_name[codigo] = nombre

    # Mapear los nombres seleccionados a sus códigos correspondientes
    selected_codes = []
    for nombre in selected_tenures:
        if nombre in name_to_code:
            selected_codes.append(name_to_code[nombre])

    # Filtrar el DataFrame por los códigos seleccionados
    df_filtered = df[df['II7'].isin(selected_codes)]

    if df_filtered.empty:
        st.warning("No hay datos para el aglomerado y los tipos de tenencia seleccionados.")
        return

    # Creo columna 'Trimestre'
    df_filtered['Trimestre'] = 'T' + df_filtered['TRIMESTRE'].astype(str)

    # Agrupar por trimestre y código de tenencia, sumando pondera
    data = df_filtered.groupby(['Trimestre', 'II7'])['PONDERA'].sum().reset_index()

    # Traduce los códigos de tenencia a nombres reales
    data['Tenencia'] = data['II7'].apply(translate_tenure)

    # Reorganizar los datos para que cada fila sea un trimestre, cada columna un tipo de tenencia, y las celdas tengan los valores ponderados
    pivot = data.pivot(index='Trimestre', columns='Tenencia', values='PONDERA')

    # Ordeno los trimestres del dataframe
    orden_trimestres = ['T1', 'T2', 'T3', 'T4']
    trimestres_presentes = [t for t in orden_trimestres if t in pivot.index]
    pivot = pivot.loc[trimestres_presentes]

    # Mostrar gráfico con la evolución según trimestres y tipo de tenencia
    st.line_chart(pivot)


def housing_report(df):
    """
    Muestra un informe con la cantidad de viviendas en villa de emergencia por aglomerado,
    incluyendo el porcentaje con respecto al total de viviendas en cada aglomerado.
    """
    if 'IV12_3' not in df.columns or 'AGLOMERADO' not in df.columns or 'PONDERA' not in df.columns:
        st.error("No se encontraron las columnas necesarias en el archivo.")
        return

    # Procesar los datos
    data = data_percentege(df)

    # Mostrar tabla ordenada
    st.dataframe(
        data[['Aglomerado', 'viviendas_en_villa', 'porcentaje_str']]
        .rename(columns={
            'viviendas_en_villa': 'Total en Villa de emergencia',
            'porcentaje_str': 'Porcentaje'
        })
    )


def data_percentege(df):
    """
    Calcula la cantidad y porcentaje de viviendas en villa de emergencia por aglomerado.
    """
    # Filtrar viviendas ubicadas en villa (IV12_3 == 1)
    df_villa = df[df['IV12_3'] == 1]

    # Total de viviendas por aglomerado
    data = df.groupby('AGLOMERADO').agg(total_viviendas=('PONDERA', 'sum'))

    # Viviendas en villa por aglomerado
    data['viviendas_en_villa'] = df_villa.groupby('AGLOMERADO')['PONDERA'].sum()
    data['viviendas_en_villa'] = data['viviendas_en_villa'].fillna(0)

    # Porcentaje (como decimal y como string)
    data['porcentaje'] = data['viviendas_en_villa'] / data['total_viviendas']
    data['porcentaje_str'] = data['porcentaje'].apply(lambda x: f"{x * 100:.2f}%")

    # Agregar nombres legibles
    data['Aglomerado'] = data.index.map(translate_aglom)
    data = data[data['Aglomerado'].notna()]

    # Ordenar de mayor a menor cantidad de viviendas en villa
    data = data.sort_values(by='viviendas_en_villa', ascending=False)

    return data


def home_percentage_per_type(df, year=None):
    """
    Calcula el porcentaje de viviendas por tipo en un año específico.
    """

    # Contar la cantidad de viviendas por tipo
    tipo_counts = df.groupby('TIPO_HOGAR')['PONDERA'].sum()

    # Lista de colores
    colores = ['#66b3ff', "#ffbffc", '#c2c2f0']

    # Ajustes para el gráfico
    fig, ax = plt.subplots(figsize=(7, 7))
    tipo_counts.plot.pie(
        autopct='%1.1f%%',
        startangle=90,
        counterclock=False,
        ax=ax,
        colors=colores[:len(tipo_counts)],
    )
    ax.set_title(
        'Proporción de viviendas según su tipo'
        + (f' - Año {year}' if year is not None else ' (Todos los años)')
    )
    ax.set_ylabel('')
    return fig


def translate_floor_type(floor_type):
    """
    Traduce el tipo de piso a un nombre más descriptivo.
    """
    if floor_type == 1:
        return 'Mosaico, Baldosa, Madera, Cerámica, Alfombra'
    elif floor_type == 2:
        return 'Cemento, Ladrillo Fino'
    elif floor_type == 3:
        return 'Ladrillo Suelto, Tierra'
    else:
        return 'Otro'


def floor_per_aglomerate(df):
    """
    Calcula el material de piso predominante por aglomerado.
    Agrupa por aglomerado y tipo de piso, sumando la ponderación
    de las viviendas.
    Para cada aglomerado, se queda con el tipo de piso con mayor ponderación.
    Devuelve un DataFrame con el aglomerado, su nombre y el material
    de piso predominante.
    """

    # Agrupa y suma la ponderación por aglomerado y tipo de piso
    # para cada combinación suma la ponderación de las viviendas
    # reset index para convertir el resultado en un DataFrame
    tabla = (
        df.groupby(['AGLOMERADO', 'IV3'])['PONDERA'].sum()
        .reset_index()
    )

    # Para cada aglomerado, se queda con el IV3 con mayor ponderación
    idx = tabla.groupby('AGLOMERADO')['PONDERA'].idxmax()
    # Filtra la tabla para quedarse solo con los índices seleccionados
    tabla = tabla.loc[idx]
    # Renombra las columnas para mayor claridad
    tabla = tabla.rename(columns={'IV3': 'Material de Piso Predominante',
                                  'AGLOMERADO': 'Aglomerado'})
    # Traducción de nombres de aglomerados y tipos de piso
    tabla['Nombre del Aglomerado'] = tabla['Aglomerado'].apply(translate_aglom)
    tabla['Material de Piso Predominante'] = (
        tabla['Material de Piso Predominante'].apply(translate_floor_type)
    )
    # Reordena las columnas
    tabla = tabla[['Aglomerado', 'Nombre del Aglomerado',
                   'Material de Piso Predominante']]

    return tabla


def show_visualizer_condition_percentage_by_agglomerate(df: pd.DataFrame):
    
    df_with_percentage_by_agglomerate = condition_percentage_by_agglomerate(df)
    fig = condigure_fig(df_with_percentage_by_agglomerate)
    return fig, df_with_percentage_by_agglomerate


def condition_percentage_by_agglomerate(df:pd.DataFrame):
    
    # agrupo las columnas de aglomerado con condicion de habitabilidad para luego sumar la columna pondera 
    # y asi obtener el total por cada condicion de habitabilidad
    df_acotado = df.groupby(["AGLOMERADO","CONDICION_DE_HABITABILIDAD"])["PONDERA"].sum().reset_index(name="VIVIENDAS_PONDERADAS")
    
    # ovtenemos el total de viviendas por aglomerado
    totales = df_acotado.groupby("AGLOMERADO")["VIVIENDAS_PONDERADAS"].sum().reset_index(name="TOTAL_AGLOMERADO")
    
    # realizo el merge entre los dataframe para realizar bien los calculos
    df_merged = pd.merge(df_acotado, totales, on="AGLOMERADO")
    
    # creao la columna porcenta y realizo el calculo del porcentaje 
    df_merged["PORCENTAJE"] = df_merged.VIVIENDAS_PONDERADAS / df_merged.TOTAL_AGLOMERADO * 100
    
    return df_merged


def condigure_fig(df: pd.DataFrame):
    
    df["AGLOMERADO_NOMBRE"] = df["AGLOMERADO"].map(translate_aglom)
    
    fig = px.bar(
        df,
        x="AGLOMERADO_NOMBRE",
        y="PORCENTAJE",
        color="CONDICION_DE_HABITABILIDAD",
        barmode="stack",
        title="Distribución porcentual de condición de habitabilidad por aglomerado"
    )
    fig.update_layout(xaxis={'type': 'category'}, xaxis_tickangle=-60,
                      xaxis_tickfont_size=9,)
    fig.update_layout(yaxis=dict(range=[0, 100]))
    
    return fig

if (__name__ == "__main__"):
    
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
    data_path = Path("merge") / "merge_hogar.csv"
    df = pd.read_csv(data_path,encoding="utf-8",sep=";")
    # un_df = condition_percentage_by_agglomerate(df)
    # print(un_df)

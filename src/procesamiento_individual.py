import csv
import os
import pandas as pd
from pathlib import Path
from src.unificacion import find_last_trim, space, percentage, section_13
from src.procesamiento_hogar import translate_aglom
from src.unificacion import sort_dict, sort_list


def process_individual_a(path_file):
    """ Recorrido de dataset de individuos, procesamiento de datos y
        agregado de columnas."""

    dict_trim = {}

    path_file = Path(path_file)
    # se define el nombre del archivo temporal
    temp_file = path_file.with_stem(path_file.stem + "_temp")

    with open(path_file, "r", encoding="utf-8", newline="") as file_in, \
            open(temp_file, "w", encoding="utf-8", newline="") as file_out:

        reader = csv.DictReader(file_in, delimiter=";")

        header = list(reader.fieldnames)

        header = header + [
            "CH04_str",
            "NIVEL_ED_str",
            "CONDICION_LABORAL",
            "UNIVERSITARIO"
        ]

        writer = csv.DictWriter(file_out, delimiter=";", fieldnames=header)
        writer.writeheader()

        for row in reader:
            row["CH04_str"] = traslate_CH04(int(row["CH04"]))
            row["NIVEL_ED_str"] = translate_education_level(
                int(row["NIVEL_ED"]))
            row["CONDICION_LABORAL"] = get_employment_status(
                int(row["ESTADO"]), int(row["CAT_OCUP"]))
            row["UNIVERSITARIO"] = is_university_student(
                int(row["NIVEL_ED"]), int(row["CH06"]))
            dict_trim = find_last_trim(row["ANO4"],
                                       row["TRIMESTRE"], dict_trim)
            writer.writerow(row)

    # se reemplaza el archivo original por los datos del _temp
    os.replace(temp_file, path_file)

    return dict_trim


def process_individual_b(path_file, dict_trim):
    """
    Procesa un archivo de datos individuales para generar estadísticas
    Parámetros:
    - path_file: ruta al archivo CSV.
    - dict_trim: diccionario con los trimestres disponibles por año.
    """
    x, y, z, year = income()

    try:
        if year not in dict_trim:
            raise ValueError("Año no válido")
    except ValueError as e:
        year = str(2024)
        print(f"Error: {e}")
        print(f"El año por defecto será: {year}")

    agglomerate = {}
    edu_agglomerate = {}
    incomplete_secondary = {}

    with open(path_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")

        for row in reader:

            agglomerate_dict(agglomerate, row)

            if int(row["AGLOMERADO"]) == x and int(row["CH06"]) >= 18:
                edu_agglomerate = sandwich(edu_agglomerate, row)

            if (
                int(row["AGLOMERADO"]) == y or int(row["AGLOMERADO"]) == z
            ) and int(row["CH06"]) >= 18:
                incomplete_secondary = load_dict(
                    row,
                    incomplete_secondary
                )

    agglomerate, edu_agglomerate, incomplete_secondary = sort_structure(
        agglomerate,
        edu_agglomerate,
        incomplete_secondary
    )
    return (
        year,
        dict_trim[year],
        agglomerate,
        y,
        edu_agglomerate,
        incomplete_secondary
    )


def main_individual_b(path_file, dict_trim, df):
    """
    Ejecuta el procesamiento de datos individual y muestra los resultados.
    Parámetros:
    - path_file: ruta al archivo CSV de datos del hogar.
    - dict_trim: diccionario el último trimestre por año.
    - df: DataFrame con los datos de los hogares.
    """
    (
        year,
        trim,
        agglomerate,
        agglomerate_name,
        edu_agglomerate,
        incomplete_secondary
    ) = process_individual_b(path_file, dict_trim)
    report_percentage(agglomerate)
    education_table(edu_agglomerate, agglomerate_name)
    secondary_percentage_table(incomplete_secondary)
    section_13(year, trim)
    año, trimestre = get_period_with_lowest_unemployment(path_file)
    print(
        f"el año y trimestre con personas con mas desocupacion es el año {año} y trimestre {trimestre}")
    top5 = get_top5_agglomerates_by_educated_households(df)
    return top5


def is_university_student(ed_level, age):
    """
    Determina si una persona es universitaria según su edad y nivel educativo.

    argumentos:
        ed_level (int): Código de nivel educativo alcanzado.
        age (int): Edad de la persona (CH06).

    retorna:
        int:
            1 si es mayor de edad y completó universidad (nivel_ed == 6),
            0 si es mayor de edad pero no completó,
            2 si no aplica (menor de edad).
    """
    if age < 18:
        return 2
    if ed_level == 6:
        return 1
    else:
        return 0


def translate_education_level(ed_level):
    """Convierte el valor de NIVEL_ED a una descripción en formato texto."""
    match ed_level:
        case 1:
            return "Primario incompleto"
        case 2:
            return "Primario completo"
        case 3:
            return "Secundario incompleto"
        case 4:
            return "Secundario completo"
        case 5 | 6:
            return "Superior o universitario"
        case 7 | 9:
            return "Sin informacion"
        case _:
            return "Desconocido"


def get_employment_status(status, occ_category):
    """
    Devuelve la condición laboral basada en los valores de ESTADO y CAT_OCUP.

    argumento:
        status (int): Valor de la columna ESTADO.
        occ_category (int): Valor de la columna CAT_OCUP.

    retorna:
        str: Condición laboral correspondiente.
    """
    if status == 1:
        if occ_category in [1, 2]:
            return "Ocupado autónomo"
        elif occ_category in [3, 4, 9]:
            return "Ocupado dependiente"
    elif status == 2:
        return "Desocupado"
    elif status == 3:
        return "Inactivo"
    elif status == 4:
        return "Fuera de categoría/sin información"
    return "Sin datos válidos"


def traslate_CH04(genero):
    """ Recibe un valor y devuelve el genero
    1: Masculino
    2: Femenino
    Caso contrario: Desconocido"""
    if genero == 1:
        return "Masculino"
    elif genero == 2:
        return "Femenino"
    else:
        return "Desconocido"


def percent_non_argentinian_with_degree(path_file):
    """retorna el porcentaje de no nacidos en argentina que hayan
    cursado un nivel unviersitario/superior
    teniendo en cuenta el año y el trimestre"""

    def evaluate_line(linea, año, trimestre):

        # este if corrobora si coinciden con el año y trimestre que se ingreso
        if int(linea["ANO4"]) == año and int(linea["TRIMESTRE"]) == trimestre:

            # una vez se sabe que corresponde a los argumentos

            # haya cursado un nivel universitario/superior -> "CH12"
            if int(linea["CH12"]) in [7, 8]:

                pondera = int(linea["PONDERA"])

                # este if corrobora que, si es una persona no nacida en Argentina -> "CH15"
                if int(linea["CH15"]) in [4, 5]:

                    # suma para total y cumplen
                    return pondera, pondera

                # solo suma al total
                return pondera, 0
        else:
            # si no coincide el año y trimestre, no suma nada
            # se retorna 0, 0 para que no afecte el total ni el cumplen
            return 0, 0
    cumplen = 0
    total = 0

    año = int(input("ingrese el año: "))

    trimestre = int(input("ingrese el trimestre: "))

    with open(path_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
    
    # en este for recorro la estructura(merge_usu_individual) que almacene en una variable, es una lista de diccionarios,
    # donde cada clave del diccionario almacena una columna
        for linea in reader:

            suma_total, suma_cumplen = evaluate_line(linea, año, trimestre)
            total += suma_total
            cumplen += suma_cumplen

    porcentaje = percentage(cumplen, total)

    print(f"En el año {año} y trimestre nro{trimestre} el porcentaje de personas no nacidas en Arg que cursaron un nivel universitario/superior fue de: {porcentaje:.2f}%")


def percent_non_argentinian_with_degree(estructura_individual):
    """retorna el porcentaje de no nacidos en argentina que hayan cursado un nivel unviersitario/superior
    teniendo en cuenta el año y el trimestre"""

    def evaluate_line(linea, año, trimestre):

        # este if corrobora si coinciden con el año y trimestre que se ingreso
        if int(linea["ANO4"]) == año and int(linea["TRIMESTRE"]) == trimestre:

            # una vez se sabe que corresponde a los argumentos

            # haya cursado un nivel universitario/superior -> "CH12"
            if int(linea["CH12"]) in [7, 8]:

                pondera = int(linea["PONDERA"])

                # este if corrobora que, si es una persona no nacida en Argentina -> "CH15"
                if int(linea["CH15"]) in [4, 5]:

                    # suma para total y cumplen
                    return pondera, pondera

                # solo suma al total
                return pondera, 0
        
        # si no coincide el año y trimestre, no suma nada
        # se retorna 0, 0 para que no afecte el total ni el cumplen
        return 0, 0
    
    cumplen = 0
    total = 0

    año = int(input("ingrese el año: "))

    trimestre = int(input("ingrese el trimestre: "))

    # en este for recorro la estructura(merge_usu_individual) que almacene en una variable, es una lista de diccionarios,
    # donde cada clave del diccionario almacena una columna
    with open(estructura_individual, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        for linea in reader:

            suma_total, suma_cumplen = evaluate_line(linea, año, trimestre)
            total += suma_total
            cumplen += suma_cumplen

    porcentaje = percentage(cumplen, total)

    print(f"En el año {año} y trimestre nro{trimestre} el porcentaje de personas no nacidas en Arg que cursaron un nivel universitario/superior fue de: {porcentaje:.2f}%")


def get_top5_agglomerates_by_educated_households(df):
    """
    Ranking de los 5 aglomerados con mayor porcentaje de hogares con dos o más
    ocupantes con estudios universitarios completos, usando los dos archivos más recientes.
    """

    # Si existe la columna 'ANO4', filtra el DataFrame para quedarse solo con los dos años más recientes
    if 'ANO4' in df.columns:
        # Obtiene los dos años más recientes
        recent_years = sorted(df['ANO4'].unique())[-2:]
        # Filtra el DataFrame por esos años
        df = df[df['ANO4'].isin(recent_years)]

    # Crea un identificador único para cada hogar combinando CODUSU y NRO_HOGAR
    df['household_id'] = list(zip(df['CODUSU'], df['NRO_HOGAR']))

    # Filtra las filas donde hay personas con universidad completa
    educated = df[df['UNIVERSITARIO'] == 1]

    # Cuenta cuántas personas con universidad completa hay por hogar
    educated_count = educated.groupby('household_id').size()

    # Asocia cada hogar a su aglomerado (elimina duplicados para no contar
    # el mismo hogar varias veces)
    # drop_duplicates asegura que cada hogar se cuenta una sola vez
    # set_index('household_id') establece el índice del DataFrame
    household_agglomerate = df.drop_duplicates(
        'household_id').set_index('household_id')['AGLOMERADO']

    # Cuenta el total de hogares por aglomerado
    total_households = df.drop_duplicates(
        'household_id').groupby('AGLOMERADO').size()

    # Selecciona los hogares que tienen 2 o más personas
    # con universidad completa
    households_with_2plus = educated_count[educated_count >= 2].index

    # Cuenta cuántos hogares con 2 o más universitarios hay por aglomerado
    agglomerate_educated = household_agglomerate.loc[households_with_2plus].value_counts()

    # Calcula el porcentaje de hogares con 2 o más universitarios
    # sobre el total de hogares por aglomerado
    porcentaje = (
        agglomerate_educated / total_households * 100
        if total_households.sum() > 0 else 0
    ).round(2)  # Redondea a dos decimales

    # Selecciona los 5 aglomerados con mayor porcentaje
    top5 = porcentaje.sort_values(ascending=False).head(5)
    # Traduce los códigos de aglomerado a nombres
    top5.index = top5.index.map(translate_aglom)
    print("Top 5 aglomerados con mayor % de hogares con 2 o más personas con universidad completa:")
    for aglomerado, porcentaje in top5.items():
        print(f"{aglomerado}: {porcentaje}%")
    return top5


def get_period_with_lowest_unemployment(pathfile):
    """
    Informa el año y trimestre con menor cantidad de personas desocupadas.
    Retorna:
        año y trimestre, 2 enteros
    """
    count_by_period = {}

    with pathfile.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:

            if row["CONDICION_LABORAL"] == "Desocupado":
                year = row["ANO4"]
                trimester = row["TRIMESTRE"]
                key = (year, trimester)

                if key in count_by_period:
                    count_by_period[key] += 1
                else:
                    count_by_period[key] = 1

    min_period = min(count_by_period.items(), key=lambda x: x[1])

    return min_period[0][0], min_period[0][1]


def adult_literacy_stats(path_file, dict_trim):
    """Calcula el porcentaje de personas adultas (mayores de 2 años) que saben leer y escribir"""

    datos = {}

    with open(path_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
    
        for linea in reader:

            pondera = int(linea["PONDERA"])
            anio = int(linea["ANO4"])

            # en este if corrobora que la linea se encuentra en el ultimo trimestre
            if int(linea["TRIMESTRE"]) == int(dict_trim[anio]):

                # como uso un diccionario contador por año corroboro que no este en el diccionario
                if not anio in datos:
                    datos[anio] = {"capaces": 0, "incapaces": 0}

                # si cumple que es mayor a 2 años -> CH06
                if int(linea["CH06"]) >= 2:
                    # y si sabe leer y escribir -> CH09
                    if int(linea["CH09"]) == 1:
                        datos[anio]["capaces"] += pondera
                    else:
                        datos[anio]["incapaces"] += pondera

    for anio, dic in datos.items():
        total_personas = dic["capaces"] + dic["incapaces"]
        if total_personas > 0:
            porcentaje_capaces = percentage(dic["capaces"], total_personas)
            porcentaje_incapaces = percentage(dic["incapaces"], total_personas)
            print(f"Año {anio}:")
            print(f"  Capaces: {porcentaje_capaces:.2f}%")
            print(f"  Incapaces: {porcentaje_incapaces:.2f}%")
        else:
            print(f"Año {anio}: No hay personas mayores de 2 años registradas.")
        print("-" * 50)


def secondary_percentage_table(incomplete_secondary):
    """
    Imprime una tabla con los porcentajes de personas con "Secundario incompleto"
    para dos aglomerados, comparando año y trimestre.
    Args:
        incomplete_secondary (dict): Diccionario con los datos de los aglomerados,
        años, trimestres, y niveles educativos.
    En caso de error imprime el mensaje: "Error: se esperaban exactamente 2 aglomerados.".
    """

    from src.unificacion import percentage
    agglomerates = list(incomplete_secondary.keys())
    percentages_aglo1 = []
    percentages_aglo2 = []
    if len(agglomerates) != 2:
        print("Error: se esperaban exactamente 2 aglomerados.")
    else:
        for year in incomplete_secondary[agglomerates[0]]:
            for row in incomplete_secondary[agglomerates[0]][year]:
                percentages_aglo1.append(
                    int(percentage(row["Secundario incompleto"], row["Total"])))
        for year in incomplete_secondary[agglomerates[1]]:
            for row in incomplete_secondary[agglomerates[1]][year]:
                percentages_aglo2.append(
                    int(percentage(row["Secundario incompleto"], row["Total"])))
        print(" ")
        print("-" * 90)
        print(
            f" {"Año":^8} | {"Trimestre":^9} | {translate_aglom(agglomerates[0]):^30} | {translate_aglom(agglomerates[1]):^30}")
        print("-" * 90)
        i = 0
        for year in incomplete_secondary[agglomerates[0]]:
            for row in incomplete_secondary[agglomerates[0]][year]:
                print(f" {year:^8} | {row['Trimestre']:^9} | {f'{percentages_aglo1[i]}%':^30} | {f'{percentages_aglo2[i]}%':^30}")
                print("-" * 90)
                i += 1


def load_dict(row, incomplete_secondary):
    """Carga los datos de un aglomerado en el diccionario `incomplete_secondary` 
    para el nivel educativo "Secundario incompleto", sumando ponderaciones por trimestre.
    Args:
        row (dict): Fila de datos que contiene el aglomerado, año, trimestre, 
        nivel educativo y ponderación.
        incomplete_secondary (dict): Diccionario que almacena los datos de 
        cada aglomerado y año, con los trimestres correspondientes.

    Returns:
        dict: El diccionario `incomplete_secondary` actualizado con los datos 
              cargados para el aglomerado y año correspondientes."""
    key = row["AGLOMERADO"]
    ano4 = row["ANO4"]
    if key not in incomplete_secondary:
        incomplete_secondary[key] = {}
    if ano4 not in incomplete_secondary[key]:
        incomplete_secondary[key][ano4] = []
    found = False
    for elem in incomplete_secondary[key][ano4]:
        if elem["Trimestre"] == int(row["TRIMESTRE"]):
            if row["NIVEL_ED_str"] == "Secundario incompleto":
                elem["Secundario incompleto"] += int(row["PONDERA"])
            elem["Total"] += int(row["PONDERA"])
            found = True
            break
    if not found:
        incomplete_secondary[key][ano4].append({"Trimestre": int(row["TRIMESTRE"]),
                                                "Secundario incompleto": int(row["PONDERA"]) if row["NIVEL_ED_str"] == "Secundario incompleto" else 0,
                                                "Total": int(row["PONDERA"])})
    return incomplete_secondary


def income():
    """Pido los ingresos necesarios para las funciones."""
    x = int(input(
        "Ingrese el número de aglomerado para mostrar los datos academicos alcanzados: "))
    y = int(input("Ingrese un aglomerado para mostrar el porcentaje de personas que no terminaron el secundario: "))
    z = int(input("Ingrese otro aglomerado para mostrar el porcentaje de personas que no terminaron el secundario: "))
    year = (input("Ingrese el año a procesar: "))
    return x, y, z, year


def sort_structure(agglomerate, edu_agglomerate, incomplete_secondary):
    """ Ordeno las estructuras de distintos incisos. """
    agglomerate = sort_dict(agglomerate)
    edu_agglomerate = sort_dict(edu_agglomerate)
    for elem in incomplete_secondary:
        incomplete_secondary[elem] = sort_dict(incomplete_secondary[elem])
        incomplete_secondary[elem] = sort_list(incomplete_secondary[elem])
    return agglomerate, edu_agglomerate, incomplete_secondary


def education_table(edu_agglomerate, agglomerate_name):
    """
    Muestro en pantalla una tabla con el nivel educativo de las personas
    del aglomerado pedido.

    argumentos:
    edu_agglomerate: Estructura para almacenar los datos necesarios
    agglomerate_name: Aglomerado enviado previamente por teclado
    """
    if len(edu_agglomerate) >= 1:
        print(" ")
        print(translate_aglom(agglomerate_name))
        print("-" * 140)
        print(
            f"  {'Año':^8} | {'Trimestre':^9} | {'Primario incompleto':^19} | "
            f"{'Primario completo':^19} | {'Secundario incompleto':^20} | "
            f"{'Secundario completo':^19} | {'Superior o universitario':^20}"
        )
        print("-" * 140)
        for year in edu_agglomerate:
            for row in edu_agglomerate[year]:
                print(
                    f"  {year:^8} | {row['Trimestre']:^9} | "
                    f"{row['Primario incompleto']:^19} | "
                    f"{row['Primario completo']:^19} | "
                    f"{row['Secundario incompleto']:^21} | "
                    f"{row['Secundario completo']:^19} | "
                    f"{row['Superior o universitario']:^20}"
                )
                print("-" * 140)
    else:
        print("Error: se esperaba un aglomerado.")


def sandwich(edu_agglomerate, row):
    """
    Agrega o actualiza los datos educativos en la estructura edu_agglomerate a partir de una fila del dataset.

    Verifica si el año y trimestre ya existen en la estructura. Si existen, actualiza los valores de los niveles educativos
    según el campo 'NIVEL_ED_str'. Si no existen, crea una nueva entrada con los valores correspondientes.

    Parámetros:
        edu_agglomerate (dict): Diccionario con los datos educativos agrupados por año.
        row (dict): Fila del dataset con información del hogar.

    Retorna:
        dict: Estructura actualizada con los datos agregados o modificados.
    """
    key = row["ANO4"]
    if key not in edu_agglomerate:
        edu_agglomerate[key] = []

    found = False
    trimestre = int(row["TRIMESTRE"])
    nivel = row["NIVEL_ED_str"]
    pondera = int(row["PONDERA"])

    for entry in edu_agglomerate[key]:
        if entry["Trimestre"] == trimestre:
            match nivel:
                case "Primario incompleto":
                    entry["Primario incompleto"] += pondera
                case "Primario completo":
                    entry["Primario completo"] += pondera
                case "Secundario incompleto":
                    entry["Secundario incompleto"] += pondera
                case "Secundario completo":
                    entry["Secundario completo"] += pondera
                case "Superior o universitario":
                    entry["Superior o universitario"] += pondera
            found = True
            break

    if not found:
        edu_agglomerate[key].append({
            "Trimestre": trimestre,
            "Primario incompleto": pondera if nivel == "Primario incompleto" else 0,
            "Primario completo": pondera if nivel == "Primario completo" else 0,
            "Secundario incompleto": pondera if nivel == "Secundario incompleto" else 0,
            "Secundario completo": pondera if nivel == "Secundario completo" else 0,
            "Superior o universitario": pondera if nivel == "Superior o universitario" else 0
        })

    return edu_agglomerate


def report_percentage(agglomerate):
    """ Muestro en pantalla el porcentaje de personas que
    cursaron el nivel universitario o superior

    argumentos:
    agglomerate : diccionario con la cantidad de personas que
    cursaron nivel universitario o superior y
    cantidad total de personas en dicho aglomerado.
    """

    from src.unificacion import percentage
    print("Porcentaje de personas que cursaron el nivel universitario o superior:")
    print("-" * 67)
    print(f"{"Aglomerado":<35}{"Porcentaje":>30}")
    print("-" * 67)
    for agglomerate_name in agglomerate:
        interested = agglomerate[agglomerate_name]["Interes"]
        total_people = agglomerate[agglomerate_name]["Total"]
        porcentaje = int(percentage(interested, total_people))
        name = translate_aglom(agglomerate_name)
        print(f"{name:<35}{porcentaje:>30}%")
    print("-" * 67)


def agglomerate_dict(agglomerate, row):
    """Agrega datos al diccionario de aglomerados."""
    key = row["AGLOMERADO"]
    if key not in agglomerate:
        agglomerate[key] = {"Total": 0, "Interes": 0}
    agglomerate[key]["Total"] += int(row["PONDERA"])
    if row["NIVEL_ED_str"] == "Superior o universitario":
        agglomerate[key]["Interes"] += int(row["PONDERA"])


def get_university_education_rate_by_agglomerate(path_file):
    """Calcula la tasa de educación universitaria por aglomerado
    a partir de un archivo CSV y devuelve un diccionario ordenado.
    """
    agglomerate = {}
    with open(path_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            agglomerate_dict(agglomerate, row)
    agglomerate = sort_dict(agglomerate)

    report_percentage(agglomerate)


def get_adult_education_level_distribution(path_file):
    """Calcula y muestra la distribución del nivel educativo de adultos
    a partir de un archivo CSV, filtrando por aglomerado y edad."""
    x = int(input(
        "Ingrese el número de aglomerado para mostrar los datos academicos alcanzados: "))
    
    edu_agglomerate = {}

    with open(path_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            try:
                if int(row["AGLOMERADO"]) == x and int(row["CH06"]) >= 18:
                    edu_agglomerate = sandwich(edu_agglomerate, row)
            except (ValueError, KeyError):
                continue 

    edu_agglomerate = sort_dict(edu_agglomerate)

    education_table(edu_agglomerate, x)


def secondary_incomplete_comparison(path_file):
    """Compara el porcentaje de personas con secundario incompleto
    en dos aglomerados diferentes a partir de un archivo CSV."""

    y = int(input("Ingrese un aglomerado para mostrar el porcentaje de personas que no terminaron el secundario: "))
    z = int(input("Ingrese otro aglomerado para mostrar el porcentaje de personas que no terminaron el secundario: "))

    incomplete_secondary = {}

    with open(path_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            if (
                int(row["AGLOMERADO"]) == y or int(row["AGLOMERADO"]) == z
            ) and int(row["CH06"]) >= 18:
                incomplete_secondary = load_dict(row, incomplete_secondary)

    for elem in incomplete_secondary:
        incomplete_secondary[elem] = sort_dict(incomplete_secondary[elem])
        incomplete_secondary[elem] = sort_list(incomplete_secondary[elem])

    secondary_percentage_table(incomplete_secondary)


def get_university_educated_in_inadequate_housing(dict_trim):
    """Calcula el porcentaje de personas con educación universitaria
    en viviendas con condicion de habitabilidad insuficiente.
    """
    year = int((input("Ingrese el año a procesar: ")))
    try:
        if year not in dict_trim:
            raise ValueError("Año no válido")
    except ValueError as e:
        year = int(2024)
        print(f"Error: {e}")
        print(f"El año por defecto será: {year}")
    section_13(year, dict_trim[year])

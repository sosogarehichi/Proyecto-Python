import csv
import os
from pathlib import Path
from src.unificacion import find_last_trim, percentage, space, open_file


def process_hogar_a(path_file):
    """
    Recorrido de dataset de hogar, procesamiento de datos y
    agregado de columnas.

    Parámetros
    path_file : Ruta al archivo.
    """

    dict_trim = {}

    path_file = Path(path_file)
    # se define el nombre del archivo temporal
    temp_file = path_file.with_stem(path_file.stem + "_temp")

    with open(path_file, "r", encoding="utf-8", newline="") as file_in, \
            open(temp_file, "w", encoding="utf-8", newline="") as file_out:

        reader = csv.DictReader(file_in, delimiter=";")

        header = list(reader.fieldnames)
        # agregar columnas nuevas a header
        header += [
            "MATERIAL_TECHUMBRE", 
            "TIPO_HOGAR", 
            "DENSIDAD_HOGAR",
            "CONDICION_DE_HABITABILIDAD"
        ]

        writer = csv.DictWriter(file_out, delimiter=";", fieldnames=header)
        writer.writeheader()

        for row in reader:
            valor = row["IV4"]
            if valor.isdigit():
                row["MATERIAL_TECHUMBRE"] = translate_material(int(valor))
            else:
                row["MATERIAL_TECHUMBRE"] = "Desconocido"
            row["TIPO_HOGAR"] = type_of_home(int(row["IX_TOT"]))
            row["DENSIDAD_HOGAR"] = density_home(density(row))
            row["CONDICION_DE_HABITABILIDAD"] = habitability_condition(
                row["IV3"], row["IV6"],
                row["IV7"], row["IV8"],
                row["IV9"], row["IV10"],
                row["IV11"],
                row["MATERIAL_TECHUMBRE"])
            dict_trim = find_last_trim(row["ANO4"],
                                       row["TRIMESTRE"], dict_trim)
            writer.writerow(row)

    # se reemplaza el archivo original por los datos del _temp
    os.replace(temp_file, path_file)

    return dict_trim


def process_hogar_b(path_file, dict_trim):
    """
    Procesa un archivo de datos del hogar para generar estadísticas
    por aglomerado y región.

    Parámetros:
    - path_file: ruta al archivo CSV.
    - dict_trim: diccionario con los trimestres disponibles por año.
    """
    data_aglom = {}
    region_data = {}
    year = input("Ingrese el año a procesar para precario_aglom: ")
    try:
        if year not in dict_trim:
            raise ValueError("Año no válido")
    except ValueError as e:
        year = str(2024)
        print(f"Error: {e}")
        print(f"El año por defecto será: {year}")

    print(f"Procesando datos para el año: {year}")

    with open(path_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")

        for row in reader:
            data_aglom = count_precario_aglom(data_aglom, row, year, dict_trim)
            region_data = tenants_in_regions(region_data, row)

    data_aglom = find_ext_material(data_aglom)
    region_data = ranking_regions(region_data)

    return data_aglom, region_data


def main_hogar_b(path_file, dict_trim):
    """
    Ejecuta el procesamiento de datos del hogar y muestra los resultados.

    Parámetros:
    - path_file: ruta al archivo CSV de datos del hogar.
    - dict_trim: diccionario el último trimestre por año.
    """
    data_aglom, region_data = process_hogar_b(path_file, dict_trim)
    print("Aglomerados con mayor y menor porcentaje de material precario:")
    print_precario_aglom(data_aglom)
    space()
    print("Ranking de inquilinos por región:")
    print_ranking(region_data)


def type_of_home(number_people):
    """Clasifica el tipo de hogar en Unipersonal, Nuclear o Extendida
    Unipersonal: 1 persona,
    Nuclear: 2 a 4 personas,
    Extendida: más de 4 personas"""
    if number_people == 1:
        return "Unipersonal"
    elif number_people <= 4:
        return "Nuclear"
    else:
        return "Extendido"


def density_home(number_of_people_for_rooms):
    """Clasifica la densidad de un hogar en Bajo, Medio o Alto
    Bajo: 1 persona por habitación o menos,
    Medio: 2 personas por habitación,
    Alto: más de 2 personas por habitación"""
    if number_of_people_for_rooms == -1:
        return "Desconocido"
    elif number_of_people_for_rooms < 1:
        return "Bajo"
    elif number_of_people_for_rooms <= 2:
        return "Medio"
    else:
        return "Alto"


def density(row):
    """Calcula la densidad de un hogar a partir de la cantidad de personas y
    habitaciones. Si no se puede calcular, devuelve 0.
    Parámetros
    row: Fila del dataset"""
    try:
        rooms_str = row["IV2"].strip()
        people_str = row["IX_TOT"].strip()

        if not people_str or not rooms_str:
            raise ValueError("Campo vacío")

        people = float(people_str)
        rooms = float(rooms_str)

        density = people / rooms if rooms != 0 else 0
    except (ValueError, ZeroDivisionError):
        density = -1
    return density


def habitability_condition(iv3, iv6, iv7, iv8, iv9, iv10,
                           iv11, material_techumbre):
    """
    Determina la condición de habitabilidad del hoga
    a partir de variables dadas.
    """

    # Por defecto asumimos condición insuficiente
    condicion = "Insuficiente"

    # Verificar si puede ser buena o saludable
    # techo durable + otras condiciones
    if iv6 == "1" and iv7 == "1" and iv8 == "1" and material_techumbre == "Material durable":
        if iv9 == "1" and iv10 == "1" and iv11 == "1" and iv3 == "1":
            condicion = "Buena"
        elif iv9 == "1" and iv10 == "2" and iv11 == "2" and iv3 == "2":
            condicion = "Saludable"

    # Verificar si puede ser regular (techo precario + otras condiciones)
    elif iv6 == "2" and iv7 == "2" and iv8 == "1":
        if iv9 == "2" and iv10 == "2" and iv11 == "3" and iv3 == "2" and material_techumbre == "Material precario":
            condicion = "Regular"

    return condicion


def translate_material(value):
    """Recibe un valor y devuelve su traducción según el material."""

    if 1 <= value <= 4:
        return "Material durable"
    if 5 <= value <= 7:
        return "Material precario"
    if 9 == value:
        return "No aplica"


def detranslate_aglom(value):
    """Recibe un valor y devuelve su traducción según el aglomerado."""
    agloms = {
        "Gran La Plata": 2,
        "Bahía Blanca - Cerri": 3,
        "Gran Rosario": 4,
        "Gran Santa Fé": 5,
        "Gran Paraná": 6,
        "Posadas": 7,
        "Gran Resistencia": 8,
        "Comodoro Rivadavia - Rada Tilly": 9,
        "Gran Mendoza": 10,
        "Corrientes": 12,
        "Gran Córdoba": 13,
        "Concordia": 14,
        "Formosa": 15,
        "Neuquén - Plottier": 17,
        "Santiago del Estero - La Banda": 18,
        "Jujuy - Palpalá": 19,
        "Río Gallegos": 20,
        "Gran Catamarca": 22,
        "Gran Salta": 23,
        "La Rioja": 25,
        "Gran San Luis": 26,
        "Gran San Juan": 27,
        "Gran Tucumán - Tafí Viejo": 29,
        "Santa Rosa - Toay": 30,
        "Ushuaia - Río Grande": 31,
        "Ciudad Autonoma de Buenos Aires": 32,
        "Partidos del GBA": 33,
        "Mar del Plata": 34,
        "Río Cuarto": 36,
        "San Nicolás - Villa Constitución": 38,
        "Rawson - Trelew": 91,
        "Viedma - Carmen de Patagones": 93
    }
    return agloms.get(value)


def translate_aglom(value):
    """Recibe un valor y devuelve su traducción según el aglomerado."""
    agloms = {
        2: "Gran La Plata",
        3: "Bahía Blanca - Cerri",
        4: "Gran Rosario",
        5: "Gran Santa Fé",
        6: "Gran Paraná",
        7: "Posadas",
        8: "Gran Resistencia",
        9: "Comodoro Rivadavia - Rada Tilly",
        10: "Gran Mendoza",
        12: "Corrientes",
        13: "Gran Córdoba",
        14: "Concordia",
        15: "Formosa",
        17: "Neuquén - Plottier",
        18: "Santiago del Estero - La Banda",
        19: "Jujuy - Palpalá",
        20: "Río Gallegos",
        22: "Gran Catamarca",
        23: "Gran Salta",
        25: "La Rioja",
        26: "Gran San Luis",
        27: "Gran San Juan",
        29: "Gran Tucumán - Tafí Viejo",
        30: "Santa Rosa - Toay",
        31: "Ushuaia - Río Grande",
        32: "Ciudad Autonoma de Buenos Aires",
        33: "Partidos del GBA",
        34: "Mar del Plata",
        36: "Río Cuarto",
        38: "San Nicolás - Villa Constitución",
        91: "Rawson - Trelew",
        93: "Viedma - Carmen de Patagones"
    }
    return agloms.get(int(value))


def count_precario_aglom(data_aglom, row, year, dict_trim):
    """
    Cuenta la cantidad de hogares con material precario por aglomerado.
    """

    max_trim = dict_trim[year]

    if row["ANO4"] == year and int(row["TRIMESTRE"]) == max_trim:
        aglom = translate_aglom(row["AGLOMERADO"])
        pond = int(row["PONDERA"])

        if aglom not in data_aglom:
            data_aglom[aglom] = {
                "material_precario": 0,
                "pondera": 0,
                "porcentaje": 0
            }

        data_aglom[aglom]["pondera"] += pond

        if row["MATERIAL_TECHUMBRE"] == "Material precario":
            data_aglom[aglom]["material_precario"] += pond

    return data_aglom


def find_ext_material(data_aglom):
    """
    Encuentra el aglomerado con el mayor y menor porcentaje
    de material precario.
    """
    aglom_max = aglom_min = None
    # calcular el porcentaje de material precario
    for aglom, datos in data_aglom.items():
        datos["porcentaje"] = percentage(datos["material_precario"],
                                         datos["pondera"])

    max = -1
    min = 9999999999

    for aglom, datos in data_aglom.items():
        if datos["porcentaje"] > max:
            max = datos["porcentaje"]
            aglom_max = aglom
        if datos["porcentaje"] < min:
            min = datos["porcentaje"]
            aglom_min = aglom
    return aglom_max, max, aglom_min, min


def print_precario_aglom(data):
    """
    Imprime una tabla con los aglomerados con mayor y menor porcentaje de material precario.
    Espera una tupla: (aglomerado_max, max, aglomerado_min, min)
    """
    print(f"{'Aglomerado':<30}{'Porcentaje material precario':>30}")
    print("-" * 60)
    aglom_max, max_pct, aglom_min, min_pct = data
    print(f"{aglom_max:<30}{max_pct:>29.2f}%")
    print(f"{aglom_min:<30}{min_pct:>29.2f}%")


def translate_region(value):
    """Recibe un valor y devuelve su traducción según la región."""
    regiones = {
        1: "Buenos Aires",
        40: "Noroeste",
        41: "Noreste",
        42: "Cuyo",
        43: "Pampeana",
        44: "Patagonia"
    }
    return regiones.get(int(value))


def tenants_in_regions(region_data, row):
    """
    Cuenta la cantidad de inquilinos por región y pondera.
    """
    region = translate_region(row["REGION"])
    tenant = int(row["II7"])
    pond = int(row["PONDERA"])

    if region not in region_data:
        region_data[region] = {
            "inquilinos": 0,
            "pondera": 0
        }

    region_data[region]["pondera"] += pond

    if tenant == 3:
        region_data[region]["inquilinos"] += pond
    return region_data


def ranking_regions(region_data):
    """
    Calcula el porcentaje de inquilinos por región y ordena el diccionario
    por el porcentaje.
    """
    for region, datos in region_data.items():
        datos["porcentaje"] = percentage(datos["inquilinos"], datos["pondera"])  # noqa

    # Ordenar el diccionario por el porcentaje de inquilinos
    region_data = dict(sorted(region_data.items(),
                              key=lambda x: x[1]["porcentaje"], reverse=True))
    return region_data


def print_ranking(data):
    """
    Imprime una tabla con los datos de inquilinos por región.
    """
    print(f"{"Región":<15}{"Porcentaje inquilinos":>25}")
    print("-" * 40)
    for region, datos in data.items():
        porcentaje = datos["porcentaje"]
        print(f"{region:<15}{porcentaje:>24.2f}%")


def report_dense_cluster_lacking_bathroom1(estructura_hogar):
    """
    Muestra el aglomerado con más viviendas que tienen más de 2 ocupantes y no tienen baño.

    Recorre una lista de hogares, cuenta cuántas personas viven en esas condiciones por aglomerado
    (usando el valor 'PONDERA'), y muestra cuál es el aglomerado con más casos.
    Parámetros:
    estructura_hogar: Lista de diccionarios que representan los hogares. """
    def mas_2_ocupantes_sin_baño(ocupantes, baño):
        return ocupantes > 2 and baño == 4

    conteo_aglomerado = {}

    # recorro la estructura
    for linea in estructura_hogar:
        aglomerado = linea["AGLOMERADO"]
        pondera = int(linea["PONDERA"])
        # verifico la condicion solicitada
        if mas_2_ocupantes_sin_baño(int(linea["IX_Tot"]), int(linea["II9"])):

            # corroboro si esta el aglomerado, si no esta, se lo agrega
            # y setea en 0
            if not (aglomerado in conteo_aglomerado):
                conteo_aglomerado[aglomerado] = 0

            # como entro al if por agloemrado le sumo pondera que indica la
            # cantidad de personas que estan en esta situacion
            conteo_aglomerado[aglomerado] += pondera

    # obtengo el aglomerado con mayor cantidad
    aglomerado_max = max(conteo_aglomerado, key=conteo_aglomerado.get)

    # obtengo la cantidad de personas del top
    cantidad_max = conteo_aglomerado[aglomerado_max]

    print(
        "Aglomerado con mayor cantidad de viviendas con más de 2 ocupantes y "
        f"sin baño: {aglomerado_max}"
    )
    print(f"Cantidad de viviendas en esa situación: {cantidad_max}")


def percentage_of_retirees_in_insufficient_by_cluster(
        path_file, dict_trim):
    """
    Calcula el porcentaje de jubilados que viven en viviendas insuficientes por aglomerado.

    Toma en cuenta solo los datos del último año y trimestre disponible según dict_trim.
    Devuelve un diccionario ordenado de mayor a menor porcentaje, con los nombres de los aglomerados.

    Parámetros:
        estructura_hogar (list): Lista de diccionarios con los datos de los hogares.
        dict_trim (dict): Diccionario donde la clave es el año y el valor es el trimestre más reciente.

    Retorna:
        resultados (dict): Diccionario con el nombre del aglomerado como clave y el porcentaje de jubilados
                           en viviendas insuficientes como valor (redondeado a dos decimales).
    """

    datos_por_aglomerado = {}

    ultimo_anio = max(anio for anio in dict_trim.keys())
    ultimo_trimestre = dict_trim[ultimo_anio]
    # a corroborar

    with open(path_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
    
        for linea in reader:

            aglomerado = int(linea["AGLOMERADO"])
            pondera = int(linea["PONDERA"])

            if int(linea["ANO4"]) == ultimo_anio and int(linea["TRIMESTRE"]) == ultimo_trimestre:

                # con este if corroboro si hay un jubilado en la vivienda
                if int(linea["V22"]) == 1:

                    # si no esta el aglomerado lo agrego
                    if aglomerado not in datos_por_aglomerado:
                        datos_por_aglomerado[aglomerado] = {"insuficientes": 0,
                                                            "noinsuficientes": 0
                                                            }

                    # voy haciendo el conteo
                    if linea["CONDICION_DE_HABITABILIDAD"] == "Insuficiente":
                        datos_por_aglomerado[aglomerado][
                            "insuficientes"
                        ] += pondera
                    else:
                        datos_por_aglomerado[aglomerado][
                            "noinsuficientes"
                        ] += pondera

    resultados = {}

    # recorro el conteo de datos por aglomerado y calculo lo pedido
    for aglomerado, dic in datos_por_aglomerado.items():
        # saco el total de personas por aglomerado
        total = dic["insuficientes"] + dic["noinsuficientes"]
        # si el aglomerado no esta vacio
        if total > 0:
            porcentaje_insuficientes = (dic["insuficientes"] / total) * 100
            # redondeo el porcentaje a dos decimales
            resultados[aglomerado] = round(porcentaje_insuficientes, 2)
        else:
            resultados[aglomerado] = None

    resultados = dict(sorted(resultados.items(), key= lambda x : x[1], reverse=True))
    
    # se le coloca el nombre del aglomerado para ser mas visible que aglomerado es
    resultados = {translate_aglom(aglomerado): nombre for aglomerado, nombre in resultados.items()}
    
    return resultados


def translate_aglom(value):
    """Recibe un valor y devuelve su traducción según el aglomerado."""
    agloms = {
        2: "Gran La Plata",
        3: "Bahía Blanca - Cerri",
        4: "Gran Rosario",
        5: "Gran Santa Fé",
        6: "Gran Paraná",
        7: "Posadas",
        8: "Gran Resistencia",
        9: "Comodoro Rivadavia - Rada Tilly",
        10: "Gran Mendoza",
        12: "Corrientes",
        13: "Gran Córdoba",
        14: "Concordia",
        15: "Formosa",
        17: "Neuquén - Plottier",
        18: "Santiago del Estero - La Banda",
        19: "Jujuy - Palpalá",
        20: "Río Gallegos",
        22: "Gran Catamarca",
        23: "Gran Salta",
        25: "La Rioja",
        26: "Gran San Luis",
        27: "Gran San Juan",
        29: "Gran Tucumán - Tafí Viejo",
        30: "Santa Rosa - Toay",
        31: "Ushuaia - Río Grande",
        32: "Ciudad Autonoma de Buenos Aires",
        33: "Partidos del GBA",
        34: "Mar del Plata",
        36: "Río Cuarto",
        38: "San Nicolás - Villa Constitución",
        91: "Rawson - Trelew",
        93: "Viedma - Carmen de Patagones"
    }
    return agloms.get(int(value))


def count_precario_aglom(data_aglom, row, year_str, year_int, dict_trim):
    max_trim = dict_trim[year_int]

    if row["ANO4"] == year_str and int(row["TRIMESTRE"]) == max_trim:
        aglom = translate_aglom(row["AGLOMERADO"])
        pond = int(row["PONDERA"])

        if aglom not in data_aglom:
            data_aglom[aglom] = {
                "material_precario": 0,
                "pondera": 0,
                "porcentaje": 0
            }

        data_aglom[aglom]["pondera"] += pond

        if row["MATERIAL_TECHUMBRE"] == "Material precario":
            data_aglom[aglom]["material_precario"] += pond

    return data_aglom


def find_ext_material(data_aglom):
    """
    Encuentra el aglomerado con el mayor y menor porcentaje
    de material precario.
    """
    aglom_max = aglom_min = None
    # calcular el porcentaje de material precario
    for aglom, datos in data_aglom.items():
        datos["porcentaje"] = percentage(datos["material_precario"],
                                         datos["pondera"])

    max = -1
    min = 9999999999

    for aglom, datos in data_aglom.items():
        if datos["porcentaje"] > max:
            max = datos["porcentaje"]
            aglom_max = aglom
        if datos["porcentaje"] < min:
            min = datos["porcentaje"]
            aglom_min = aglom
    return aglom_max, max, aglom_min, min


def translate_region(value):
    """Recibe un valor y devuelve su traducción según la región."""
    regiones = {
        1: "Buenos Aires",
        40: "Noroeste",
        41: "Noreste",
        42: "Cuyo",
        43: "Pampeana",
        44: "Patagonia"
    }
    return regiones.get(int(value))


def tenants_in_regions(region_data, row):
    """
    Cuenta la cantidad de inquilinos por región y pondera.
    """
    region = translate_region(row["REGION"])
    if row["II7"].isdigit():
        tenant = int(row["II7"])
    else:
        tenant = 0
    pond = int(row["PONDERA"])

    if region not in region_data:
        region_data[region] = {
            "inquilinos": 0,
            "pondera": 0
        }

    region_data[region]["pondera"] += pond

    if tenant == 3:
        region_data[region]["inquilinos"] += pond
    return region_data


def ranking_regions(region_data):
    """
    Calcula el porcentaje de inquilinos por región y ordena el diccionario
    por el porcentaje.
    """
    for region, datos in region_data.items():
        datos["porcentaje"] = percentage(datos["inquilinos"], datos["pondera"])  # noqa

    # Ordenar el diccionario por el porcentaje de inquilinos
    region_data = dict(sorted(region_data.items(),
                              key=lambda x: x[1]["porcentaje"], reverse=True))
    return region_data


def print_ranking(data):
    """
    Imprime una tabla con los datos de inquilinos por región.
    """
    print(f"{"Región":<15}{"Porcentaje inquilinos":>25}")
    print("-" * 40)
    for region, datos in data.items():
        porcentaje = datos["porcentaje"]
        print(f"{region:<15}{porcentaje:>24.2f}%")


def report_dense_cluster_lacking_bathroom2(path_file):
    """
    Muestra qué aglomerado tiene más viviendas con más de 2 ocupantes y sin baño.

    Parámetros:
        estructura_hogar (list): Lista de diccionarios con datos de cada hogar.
    """
    def mas_2_ocupantes_sin_baño(ocupantes, baño):
        return ocupantes > 2 and baño == 4

    conteo_aglomerado = {}

    with open(path_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
    # recorro la estructura
        for linea in reader:
            aglomerado = linea["AGLOMERADO"]
            pondera = int(linea["PONDERA"])
            # verifico la condicion solicitada
            if mas_2_ocupantes_sin_baño(int(linea["IX_TOT"]), int(linea["II9"])):

                # corroboro si esta el aglomerado, si no esta, se lo agrega y setea en 0
                if not (aglomerado in conteo_aglomerado):
                    conteo_aglomerado[aglomerado] = 0

                # como entro al if por agloemrado le sumo pondera que indica la cantidad de personas que estan en esta situacion
                conteo_aglomerado[aglomerado] += pondera

    # obtengo el aglomerado con mayor cantidad
    aglomerado_max = max(conteo_aglomerado, key=conteo_aglomerado.get)

    # obtengo la cantidad de personas del top
    cantidad_max = conteo_aglomerado[aglomerado_max]

    print(
        f"Aglomerado con mayor cantidad de viviendas con más de 2 ocupantes y sin baño fue: {translate_aglom(aglomerado_max)}")
    print(f"Cantidad de viviendas en esa situación: {cantidad_max}")


def report_owner_occupancy_percentage(file_path):
    """
    Para cada aglomerado, informa el porcentaje de viviendas ocupadas por sus propietarios,
    considerando la ponderación y mostrando los nombres de aglomerados.
    """

    # Contadores ponderados por aglomerado
    total_homes = {}         # Aglomerado -> suma de ponderaciones totales
    owner_occupied = {}      # Aglomerado -> suma de ponderaciones de propietarios

    with file_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:
            aglo = int(row["AGLOMERADO"])
            ownership_code = row["II7"]    # Código correcto de tenencia
            pondera = int(row["PONDERA"])  # Ponderación

            # Inicializar si es la primera vez que vemos este aglomerado
            if aglo not in total_homes:
                total_homes[aglo] = 0
                owner_occupied[aglo] = 0

            total_homes[aglo] += pondera

            # Si es propietario (II7 == "1" o "2"), sumar al contador de dueños
            if ownership_code in ("1", "2"):
                owner_occupied[aglo] += pondera

    # Calcular porcentaje y mostrar
    print("Porcentaje de viviendas ocupadas por sus propietarios por aglomerado:")
    for aglo in total_homes:
        total = total_homes[aglo]
        owners = owner_occupied[aglo]
        if total > 0:
            percentage = (owners / total) * 100
        else:
            percentage = 0

        # Mostrar nombre de aglomerado y el porcentaje redondeado sin decimales
        aglo_name = translate_aglom(aglo)
        print(f"{aglo_name}: {int(round(percentage))} %")


def get_agglomerates_by_precario_material_extremes(path_file, dict_trim):
    """
    Imprime el aglomerado con mayor y menor porcentaje de viviendas de material precario
    en el último trimestre disponible del año ingresado.

    Parámetros:
    - path_file: Ruta al archivo CSV.
    - dict_trim: Diccionario con los trimestres disponibles por año.
    """
    data_aglom = {}
    year_input = input("Ingrese el año a procesar para precario_aglom: ")

    try:
        year_int = int(year_input)
        if year_int not in dict_trim:
            raise ValueError("Año no válido")
    except ValueError as e:
        year_int = 2024
        print(f"Error: {e}")
        print(f"El año por defecto será: {year_int}")

    year_str = str(year_int)
    print(f"Procesando datos para el año: {year_str}")

    with open(path_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            data_aglom = count_precario_aglom(data_aglom, row, year_str, year_int, dict_trim)

    extremos_aglom = find_ext_material(data_aglom)
    print("Aglomerados con mayor y menor porcentaje de material precario:")
    print_precario_aglom(extremos_aglom)


def sort_regions_by_tenant_percentage_desc(path_file):
    """Ordena las regiones por el porcentaje de inquilinos y muestra el ranking."""
    region_data = {}
    with open(path_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            region_data = tenants_in_regions(region_data, row)
    
    region_data = ranking_regions(region_data)
    print("Ranking de inquilinos por región:")
    print_ranking(region_data)

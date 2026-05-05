import csv
from pathlib import Path


def add_file(file, file_out, file_exists):
    """
    Agrega el contenido de un file CSV de entrada a un file de salida.

    Lee un file CSV separado por punto y coma (;) y lo escribe en el file
    de salida especificado. Si el file de salida no existe aún (indicado por
    `file_exists`), se escribe también la fila de header.

    Parámetros:
    ----------
    file : Path
        Ruta del archivo de entrada que se desea agregar.
    file_out : Path
        Ruta del archivo de salida al que se agregará el contenido.
    file_exists : bool
        Indica si el archivo de salida ya existe (True) o si se está
        escribiendo por primera vez (False).
    """
    # Abrir archivos
    with open(file, 'r', encoding='utf-8') as f_in, \
            open(file_out, 'a', encoding='utf-8', newline='') as f_out:
        # a = modo append -> para agregarlo al final

        reader = csv.reader(f_in, delimiter=';', quotechar='"')
        writer = csv.writer(f_out, delimiter=';', quotechar='"')
        # quoteminimal -> para mantener al mínimo las comillas
        # Leer header
        header = next(reader)

        # Escribir header solo si el file de salida no existe aún
        if not file_exists:
            writer.writerow(header)
        # Escribir el resto de las filas
        for fila in reader:
            writer.writerow(fila)

# a los archivos nuevos se debe chequear si existen,
#  procesar (agregar las columnas) y luego agregar al dataset


def merge_data(folder_in, folder_out):
    """
    Recorre todos los archivos en una carpeta de entrada y los fusiona
    en dos archivos de salida.

    Clasifica los archivos según si contienen la palabra "hogar" en el nombre
    y los agrupa en dos archivos separados: uno para datos de hogar y otro
    para datos individuales.
    Los archivos de salida se crean en una carpeta de salida definida
    en una variable.
    Si los archivos de salida ya existen, se eliminan antes de
    escribir los nuevos.

    Utiliza la función `add_file()`
    para agregar los contenidos.
    """

    # carpetas de salida
    file_individual = folder_out / "merge_individual.csv"
    file_hogar = folder_out / "merge_hogar.csv"

    if file_individual.exists():
        file_individual.unlink()
        print(f"{file_individual.name} eliminado.")
    if file_hogar.exists():
        file_hogar.unlink()
        print(f"{file_hogar.name} eliminado.")

    file_hogar_exists = False
    file_ind_exists = False

    # Recorrer todos los archivos (no carpetas)
    for file in folder_in.iterdir():
        if file.is_file() and file.suffix == '.txt':
            print("Archivo encontrado:", file.name)
            if "hogar" in file.name:
                add_file(file, file_hogar, file_hogar_exists)
                file_hogar_exists = True
                print("Archivo agregado correctamente a:", file_hogar)
            elif "individual" in file.name:
                add_file(file, file_individual, file_ind_exists)
                file_ind_exists = True
                print("Archivo agregado correctamente a:", file_individual)


def add_column(data, path_file):
    """
    Agrega una columna al archivo CSV de salida con el nombre del archivo
    de entrada y el año correspondiente.
    Se utiliza para identificar el origen de los datos en el archivo
    resultante.
    Parámetros:
    ----------
    data : list
        Lista de diccionarios que representan las filas del archivo CSV.
    path_file : Path
        Ruta del archivo CSV de salida.
    """
    header = list(data[0].keys())

    with open(path_file, 'w', encoding="utf-8", newline='') as file:
        # con fieldnames dicto las claves y cual va a ser la orden de lectura
        writer = csv.DictWriter(file, fieldnames=header, delimiter=";")
        writer.writeheader()  # aplico el encabezado
        writer.writerows(data)


def percentage(interes, total):
    """
    Calcula el porcentaje de un interés respecto a un total.
    """
    return (interes / total) * 100 if total != 0 else 0


def find_last_trim(year, trimester, dict_trim):
    """
    Encuentra el último trimestre de un año en los datos.
    """

    if year not in dict_trim:
        dict_trim[year] = int(trimester)
    else:
        if int(trimester) > dict_trim[year]:
            dict_trim[year] = int(trimester)
    return dict_trim


def show_range():
    """
    Recorre todos los archivos en la carpeta de entrada y determina el
    rango de years y trimestres presentes en los datos.
    Devuelve un string con el rango de years y trimestres.
    """
    max_trim = None
    min_year = None
    max_year = None
    min_trim = None

    # debe hacerse path, pq sino es solo un string
    folder_in = Path("merge")

    for file in folder_in.iterdir():
        print(file.name)
        with open(file, 'r', encoding='utf-8') as f_in:
            reader = csv.reader(f_in, delimiter=';', quotechar='"')
            # se necesita el header para obtener los indices
            header = next(reader)
            try:
                # Obtenemos los índices de las columnas
                idx_year = header.index("ANO4")
                idx_trim = header.index("TRIMESTRE")
            except ValueError:
                print("Las columnas 'ANO4' o 'TRIMESTRE' no"
                      f"se encuentran en {file.name}")
                continue  # Si no se encuentran, saltamos este file

            for row in reader:
                try:
                    # Intentar convertir los valores a int
                    year = int(row[idx_year])
                    trim = int(row[idx_trim])
                except (ValueError, IndexError):
                    # Si hay algún error (valor no numérico o índice fuera
                    #  de rango), salta esta fila
                    continue
                # si el año es el mínimo se actualiza con trimestre y todo
                # si es igual al mínimo se comparan los trimestres
                if min_year is None:
                    min_year, max_year = year, year
                    min_trim, max_trim = trim, trim
                else:
                    if (year < min_year) or (year == min_year and
                                             trim < min_trim):
                        min_year = year
                        min_trim = trim
                    # si el year es el mayo se actualiza con trimestre y todo
                    # si el year es igual al mayor se comparan los trimestres
                    if (year > max_year) or (year == max_year and
                                             trim > max_trim):
                        max_year = year
                        max_trim = trim
    return (
        (
            "El sistema contiene información desde el"
            f" trimestre {min_trim} de {min_year}"
            f" hasta el trimestre {max_trim} de {max_year}."
        )
    )


def path_file(sufix):
    """
    Devuelve la ruta del archivo de salida según el sufijo proporcionado.
    Se utiliza para construir la ruta del archivo de salida en función
    del sufijo especificado.
    Parámetros:
    ----------
    sufix : str
        Sufijo del archivo de salida (por ejemplo, "merge_hogar.csv").
    """
    path = Path(__file__).resolve().parent.parent
    return path / 'merge' / sufix


def space():
    """
    Imprime un espacio en blanco para separar secciones.
    """
    print("\n")


def sort_dict(diccionario):
    """Ordena un diccionario"""
    return dict(sorted(diccionario.items(), key=lambda x: int(x[0])))


def sort_list(edu_agglomerate):
    """Ordena las listas de cada año por el valor del 'Trimestre'."""
    for year in edu_agglomerate:
        edu_agglomerate[year] = sorted(
            edu_agglomerate[year], key=lambda x: x['Trimestre'])
    return edu_agglomerate


def section_13(year, quarter):
    """Muestro la cantidad de personas con nivel 'Superior o universitario'
    que viven en viviendas con condición de habitabilidad 'Insuficiente',
    para un año y trimestre dados."""
    path_household_file = path_file('merge_hogar.csv')
    path_individual_file = path_file('merge_individual.csv')
    codusu = {}
    count = 0

    with open(path_individual_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')

        for row in reader:
            if (
                year == int(row['ANO4'])
                and quarter == int(row['TRIMESTRE'])
                and row['NIVEL_ED_str'] == "Superior o universitario"
            ):
                if row['CODUSU'] not in codusu:
                    codusu[row['CODUSU']] = int(row['PONDERA'])
                else:
                    codusu[row['CODUSU']] += int(row['PONDERA'])

    with open(path_household_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')

        for row in reader:
            if (
                row['CODUSU'] in codusu
                and year == int(row['ANO4'])
                and quarter == int(row['TRIMESTRE'])
                and row['CONDICION_DE_HABITABILIDAD'] == "Insuficiente"
            ):
                count += codusu[row['CODUSU']]

    print()
    print(
        f'La cantidad de personas con nivel "Superior o universitario" '
        f'con condicion de habitabilidad "Insuficiente" son: {count}'
    )


def open_file(path_file):

    with open(path_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")

    return reader


def checking_twins():
    """
    Revisa la carpeta de datos para encontrar inconsistencias entre los
    archivos de hogar e individual. Busca archivos que deberían estar
    emparejados (hogar e individual) y reporta si falta alguno de ellos.
    Devuelve una lista de inconsistencias encontradas.
    """

    folder_in = Path("data")

    hogares = []
    individuales = []
    inconsistencias = []

    for file in folder_in.iterdir():
        if file.name.endswith(".txt"):
            parts = file.stem.split("_")
            # stem es el nombre del archivo sin la extensión
            if len(parts) < 3:
                continue
            anio_trimestre = parts[2]
            if "hogar" in file.name:
                hogares.append(anio_trimestre)
            elif "individual" in file.name:
                individuales.append(anio_trimestre)

    for hogar in hogares:
        if hogar not in individuales:
            inconsistencias.append(f"Falta archivo individual para {hogar}")

    for individual in individuales:
        if individual not in hogares:
            inconsistencias.append(f"Falta archivo hogar para {individual}")

    return inconsistencias


def dict_years_trimesters(df):
    """
    Devuelve un diccionario {año: [trimestres]} a partir de un DataFrame
    con columnas 'ANO4' y 'TRIMESTRE'.
    """
    dicc = {}
    # para cada año que se encuentre de forma única en el DataFrame
    for year in sorted(df["ANO4"].unique()):
        # Filtra el DataFrame para el año actual y obtiene los
        # trimestres de ese año
        trimestres = df.loc[df["ANO4"] == year, "TRIMESTRE"].unique()
        # Convierte los trimestres a enteros, los ordena y los asigna
        # como valor del año en el diccionario
        dicc[int(year)] = sorted([int(t) for t in trimestres])
    return dicc


def muestra_aglomerados(df):
    """Muestra los aglomerados disponibles en el DataFrame."""
    from src.procesamiento_hogar import translate_aglom
    aglom = df['AGLOMERADO'].unique().tolist()
    aglom.sort()
    print("Aglomerados disponibles:")
    print(f"{"Aglomerado":<35}{"Numero":>10}")
    print("-" * 45)
    for agglomerate in aglom:
        print(f"{translate_aglom(agglomerate):<35}{agglomerate:>10}")
    print("-" * 45)


def years(df):
    """Muestra los años disponibles en el DataFrame."""
    year = df['ANO4'].unique().tolist()
    year.sort()
    print("Años disponibles:")
    print(year)


def muestra(df):
    """Muestra los aglomerados y años disponibles en el DataFrame."""
    muestra_aglomerados(df)
    years(df)

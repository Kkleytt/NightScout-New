from prettytable import PrettyTable  # Библиотека для вывода таблиц в консоль
from database import database as db  # Библиотека для работы с БД
import commentjson as json  # Библиотека для работы с JSON-строками
import os  # Библиотека для работы с файловой системы


# Функция чтения конфига в нужной директории
def read_config():
    """
    Функция для считывания данных JSON с файла настроек с поддержкой комментариев
    :return: Словарь с конфигурационными данными
    """

    work_dir = os.getcwd()  # Текущая рабочая директория
    module = "move"  # Имя поддиректории с модулем
    filename = "config.json"  # Имя конфига

    # Формируем абсолютный путь к config.json внутри модуля
    absolute_path = os.path.abspath(os.path.join(work_dir, module, filename))

    try:
        with open(absolute_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f'Ошибка чтения конфигурационного файла: {e}')
        exit(101)


# Функция создания таблиц в MySQL
def create_tables(connection, cursor, sugar=False, insulin=False, device=False):
    """
    Функция создания таблиц в MySQL
    :param connection: Объект соединения БД (MySQL)
    :param cursor: Объект курсора БД (MySQL)
    :param sugar: Параметр создания таблицы сахаров
    :param insulin: Параметр создания таблицы инсулина и еды
    :param device: Параметр создания таблицы устройств
    :return: None
    """

    try:
        if sugar:
            query = """CREATE TABLE Sugar (
                    id TEXT,
                    date TEXT,
                    sugar FLOAT,
                    tendency TEXT,
                    difference TEXT
                    )"""
            db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query
            )

        if insulin:
            query = """CREATE TABLE Insulin (
                    id TEXT,
                    date TEXT,
                    base FLOAT,
                    insulin FLOAT,
                    carbs FLOAT,
                    duration INT,
                    type TEXT
                    )"""
            db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query
            )

        if device:
            query = """CREATE TABLE Device (
                    id INT,
                    date TEXT,
                    phone_battery INT,
                    transmitter_battery INT,
                    pump_battery INT,
                    pump_cartridge INT,
                    cannula TEXT,
                    insulin TEXT,
                    sensor TEXT,
                    pump_model TEXT,
                    phone_model TEXT,
                    transmitter_model TEXT
                    )"""
            db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query
            )
    except Exception as e:
        print(f"Ошибка создания таблиц в MySQL - {e}")
        exit(302)


# Функция очистки таблиц MySQL
def reset_table(connection, cursor, sugar=False, insulin=False, device=False):
    """
    Функция очистки таблиц MySQL
    :param connection: Объект соединения БД (MySQL)
    :param cursor: Объект курсора БД (MySQL)
    :param sugar: Параметр очистки таблицы сахаров
    :param insulin: Параметр очистки таблицы инсулина и еды
    :param device: Параметр очистки таблицы устройств
    :return: None
    """

    if sugar:
        query = "DELETE FROM Sugar"
        db.send_request_db(
            connection=connection,
            cursor=cursor,
            query=query
        )

    if insulin:
        query = "DELETE FROM Insulin"
        db.send_request_db(
            connection=connection,
            cursor=cursor,
            query=query
        )

    if device:
        query = "DELETE FROM Device"
        db.send_request_db(
            connection=connection,
            cursor=cursor,
            query=query
        )


# Функция удаления таблиц MySQL
def drop_table(connection, cursor, sugar=False, insulin=False, device=False):
    """
    Функция удаления таблиц MySQL
    :param connection: Объект соединения БД (MySQL)
    :param cursor: Объект курсора БД (MySQL)
    :param sugar: Параметр удаления таблицы сахаров
    :param insulin: Параметр удаления таблицы инсулина и еды
    :param device: Параметр удаления таблицы устройств
    :return: None
    """

    if sugar:
        query = "DROP TABLE Sugar"
        db.send_request_db(
            connection=connection,
            cursor=cursor,
            query=query
        )

    if insulin:
        query = "DROP TABLE Insulin"
        db.send_request_db(
            connection=connection,
            cursor=cursor,
            query=query
        )

    if device:
        query = "DROP TABLE Device"
        db.send_request_db(
            connection=connection,
            cursor=cursor,
            query=query
        )


# Функция переноса данных из SqLite в MySQL
def start_moving(connection, cursor, connection_sqlite, cursor_sqlite, sugar=False, insulin=False, device=False):
    """
    Функция переноса данных из SqLite в MySQL
    :param connection: Объект соединения БД (MySQL)
    :param cursor: Объект курсора БД (MySQL)
    :param connection_sqlite: Объект соединения БД (SqLite)
    :param cursor_sqlite: Объект курсора БД (SqLite)
    :param sugar: Параметр переноса таблицы сахаров
    :param insulin: Параметр переноса таблицы инсулина и еды
    :param device: Параметр переноса таблицы устройств
    :return: None
    """

    try:
        if sugar:
            print("\nПеренос данных сахаров...")

            # Получение всех данных сахаров из SqLite
            query = "SELECT * FROM Sugar"
            results = db.send_request_db(
                connection=connection_sqlite,
                cursor=cursor_sqlite,
                query=query
            )

            # Перебор строк сахаров в SqLite и сохранение в MySQL
            for item in results:
                query = """INSERT INTO Sugar values (%s, %s, %s, %s, %s)"""
                new_str = [
                    item[0] if item[0] != 'None' else None,
                    item[1] if item[1] != 'None' else None,
                    item[2] if item[2] != 'None' else None,
                    item[3] if item[3] != 'None' else None,
                    item[4] if item[4] != 'None' else None
                ]
                db.send_request_db(
                    connection=connection,
                    cursor=cursor,
                    query=query,
                    data=new_str
                )
            print("--- База данных сахаров успешно перенесена")

        if insulin:
            print("\nПеренос базы данных инсулина...")

            # Получение всех данных инсулина и еды из SqLite
            query = "SELECT * FROM Insulin"
            results = db.send_request_db(
                connection=connection_sqlite,
                cursor=cursor_sqlite,
                query=query
            )

            # Перебор строк инсулина и еды в SqLite и сохранение в MySQL
            for item in results:
                query = """INSERT INTO Insulin values (%s, %s, %s, %s, %s, %s, %s)"""
                item = list(item)
                try:
                    # Проверка столбца с временем действия события
                    item[5] = item[5] if item[5] != 'None' else None
                    try:
                        if item[5] is not None:
                            item[5].replace("min", '')
                    finally:
                        pass

                    new_str = [
                        item[0] if item[0] != 'None' else None,
                        item[1] if item[1] != 'None' else None,
                        item[2] if item[2] != 'None' else None,
                        item[3] if item[3] != 'None' else None,
                        item[4] if item[4] != 'None' else None,
                        item[5] if item[5] != 'None' else None,
                        item[6] if item[6] != 'None' else None
                    ]
                    db.send_request_db(
                        connection=connection,
                        cursor=cursor,
                        query=query,
                        data=new_str
                    )
                except Exception as e:
                    print(item, e)
            print("--- База данных инсулина успешно перенесена")

        if device:
            print("\nПеренос базы данных устройств...")

            # Получение всех данных инсулина и еды из SqLite
            query = "SELECT * FROM Device"
            results = db.send_request_db(
                connection=connection_sqlite,
                cursor=cursor_sqlite,
                query=query
            )
            item = list(results[0])

            try:
                query = """INSERT INTO Device values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                db.send_request_db(
                    connection=connection,
                    cursor=cursor,
                    query=query,
                    data=item
                )
                print("--- База данных устройств успешно перенесена")
            except Exception as e:
                print(item, e)

    except Exception as e:
        print(f"Ошибка перемещения данных - {e}")
        exit(401)


# Функция сравнения кол-во данных в SqLite и MySQL
def check_status(connection, cursor, connection_sqlite, cursor_sqlite):
    """
    Функция сравнения кол-во данных в SqLite и MySQL
    :param connection: Объект соединения БД (MySQL)
    :param cursor: Объект курсора БД (MySQL)
    :param connection_sqlite: Объект соединения БД (SqLite)
    :param cursor_sqlite: Объект курсора БД (SqLite)
    :return: None
    """

    try:
        # Получение данных из MySQL
        sugar_mysql = db.send_request_db(
            connection=connection,
            cursor=cursor,
            query="SELECT id FROM Sugar"
        )
        insulin_mysql = db.send_request_db(
            connection=connection,
            cursor=cursor,
            query="SELECT id FROM Insulin"
        )
        device_mysql = db.send_request_db(
            connection=connection,
            cursor=cursor,
            query="SELECT id FROM Device"
        )

        # Получение данных из SqLite
        sugar_sqlite = db.send_request_db(
            connection=connection_sqlite,
            cursor=cursor_sqlite,
            query="SELECT id FROM Sugar"
        )
        insulin_sqlite = db.send_request_db(
            connection=connection_sqlite,
            cursor=cursor_sqlite,
            query="SELECT id FROM Insulin"
        )
        device_sqlite = db.send_request_db(
            connection=connection_sqlite,
            cursor=cursor_sqlite,
            query="SELECT id FROM Device"
        )

        # Создание таблицы сравнения кол-во данных
        table = PrettyTable()
        table.field_names = ['Таблица', 'SqLite', 'MySQL']
        table.add_row(['Сахара', len(sugar_sqlite), len(sugar_mysql)])
        table.add_row(['Инсулин', len(insulin_sqlite), len(insulin_mysql)])
        table.add_row(['Устройства', len(device_sqlite), len(device_mysql)])

        # Вывод сравнительной таблицы
        print(table, "\n")

    except Exception as e:
        print(f"Ошибка сравнения данных - {e}")
        exit(501)


# Старт программы
def start(connection_mysql, cursor_mysql, connection_sqlite, cursor_sqlite):
    # Чтение настроек модуля
    data = read_config()

    # Проверка на очистку таблицы
    if data['reset']:
        # Очистка базы MySQL
        reset_table(
            connection=connection_mysql,
            cursor=cursor_mysql,
            sugar=data['move']['sugar'],
            insulin=data['move']['insulin'],
            device=data['move']['device']
        )
        # Удаление таблиц MySQL
        drop_table(
            connection=connection_mysql,
            cursor=cursor_mysql,
            sugar=data['move']['sugar'],
            insulin=data['move']['insulin'],
            device=data['move']['device']
        )

        # Создание новых таблиц
        create_tables(
            connection=connection_mysql,
            cursor=cursor_mysql,
            sugar=data['move']['sugar'],
            insulin=data['move']['insulin'],
            device=data['move']['device']
        )

    # Перемещение данных из SqLite в MySQL
    start_moving(
        connection=connection_mysql,
        cursor=cursor_mysql,
        connection_sqlite=connection_sqlite,
        cursor_sqlite=cursor_sqlite,
        sugar=data['move']['sugar'],
        insulin=data['move']['insulin'],
        device=data['move']['device']
    )

    # Сравнение кол-во данных в SqLite и MySQL
    check_status(
        connection=connection_mysql,
        cursor=cursor_mysql,
        connection_sqlite=connection_sqlite,
        cursor_sqlite=cursor_sqlite
    )

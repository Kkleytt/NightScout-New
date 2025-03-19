import commentjson as json  # Библиотека для работы с JSON-строками
import os  # Библиотека для работы с файловой системой
import pymysql  # Библиотека для работы с БД (MySQL)


# Функция чтения конфига в нужной директории
def read_config():
    """
    Функция для считывания данных JSON с файла настроек с поддержкой комментариев
    :return: Словарь с конфигурационными данными
    """

    work_dir = os.getcwd()  # Текущая рабочая директория
    module = "database"  # Имя поддиректории с модулем
    filename = "config.json"  # Имя конфига

    # Формируем абсолютный путь к config.json внутри модуля
    absolute_path = os.path.abspath(os.path.join(work_dir, module, filename))

    try:
        with open(absolute_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f'Ошибка чтения конфигурационного файла: {e}')
        exit(101)


# Функция подключения к MySQL
def connect_mysql():
    """
    Функция подключения к БД (MySQL)
    :return: MySQL-connection
    """

    # Чтение настроек подключения к MySQL
    data = read_config()

    # Попытка подключения
    try:
        con = pymysql.connect(
            host=data['mysql']['host'],
            port=data['mysql']['port'],
            user=data['mysql']['user'],
            password=data['mysql']['password'],
            database=data['mysql']['database'],
            connect_timeout=data['mysql']['timeout'],
            read_timeout=data['mysql']['read_timeout'],
            write_timeout=data['mysql']['write_timeout'],
        )
        cur = con.cursor()
        return con, cur

    except Exception as e:
        print(f"Неудачное подключение к БД - {e}")
        return None, None


# Функция отправки запросов в БД
def send_request_db(connection, cursor, query, data=None):
    """
    Функция отправки запросов в БД
    :param connection: Объект соединения БД
    :param cursor: Объект курсора БД
    :param query: Запрос дял выполнения
    :param data: Данные для запроса
    :return: Данные из БД
    """

    # Попытка отправить запрос и сохранить изменения
    try:
        cursor.execute(query, data)
        connection.commit()
        return cursor.fetchall()
    except Exception as e:
        print(f"Ошибка отправки запроса MySQL - {e}")
        connection.rollback()
        return None

from gui import cli
from gui import stats
from parser import parse
from move import move
from database import database as db
import json
import argparse
import time


# Чтение глобальных настроек программы
def read_config():
    """
    Функция для считывания данных JSON с файла настроек
    :return: JSON массив данных
    """

    try:
        file = "config.json"
        with open(file, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f'Ошибка чтения конфигурационного файла - {e}')
        exit(101)


# Функция запуска программы с пользовательским вводом команд
def start_loop(connection, cursor, settings):
    """
    Функция запуска программы без аргументов при запуске
    :param connection: Объект подключения БД (MySQL)
    :param cursor: Объект курсора БД (MySQL)
    :param settings: JSON-строка с настройками программы
    :return: None
    """

    # Вывод таблицы команд
    table_help = "\nТаблица команд:\n"\
                 "1) /parse - Получить и сохранить данные\n"\
                 "2) /print - Вывести данные в консоль\n"\
                 "3) /move - Перенести данные с SqLite в MySQL\n"\
                 "4) /stats - Вывести график сахаров за последний день\n"\
                 "5) /parse/loop - Запустить цикл получения и сохранения данных\n"\
                 "6) /print/loop - Запустить цикл получения, сохранения и вывода данных\n"\
                 "7) /help - Вывести данную таблицу"
    print(table_help)

    while True:

        user_input = str(input("Введите команду - "))

        # Обработка введенной команды пользователем
        match user_input:
            case "/parse":
                parse.start(
                    connection=connection,
                    cursor=cursor
                )

            case "/print":
                cli.show(
                    connection=connection,
                    cursor=cursor
                )

            case "/move":
                connection_sqlite, cursor_sqlite = db.connect_sqlite()
                move.start(
                    connection_mysql=connection,
                    cursor_mysql=cursor,
                    connection_sqlite=connection_sqlite,
                    cursor_sqlite=cursor_sqlite
                )
                db.close_sqlite(connection_sqlite)

            case "/stats":
                stats.start(
                    connection=connection,
                    cursor=cursor
                )

            case "/parse/loop":
                while True:
                    parse.start(
                        connection=connection,
                        cursor=cursor
                    )
                    time.sleep(settings['loop_timeout'])

            case "/print/loop":
                while True:
                    parse.start(
                        connection=connection,
                        cursor=cursor
                    )
                    cli.show(
                        connection=connection,
                        cursor=cursor
                    )
                    time.sleep(settings['loop_timeout'])

            case "/help":
                print(table_help)

            case _:
                print(f"--- Неверная команда '{user_input}'")


# Функция запуска программы с аргументами
def start():
    # Чтение настроек программы
    settings = read_config()

    # Подключение к БД (MySQL)
    connection, cursor = db.connect_mysql()
    if connection is None or cursor is None:
        exit(1001)

    # Обработка входных команд при запуске
    parser = argparse.ArgumentParser(description="Process commands for Diabetes program")
    parser.add_argument(
        "command",
        help="Command to execute",
        nargs="?",  # Сделать аргумент необязательным
        default="--noneArgs",  # Указать значение по умолчанию, если аргумент отсутствует
        choices=["--parse", "--print", "--move", "--stats", "--parseLoop", "--printLoop", "--help", "--noneArgs"]
    )
    args = parser.parse_args()
    arg = args.command

    # Проверка на входные значения при запуске программы
    match arg:
        case "--parse":
            parse.start(
                connection=connection,
                cursor=cursor
            )

        case "--print":
            cli.show(
                connection=connection,
                cursor=cursor
            )

        case "--move":
            connection_sqlite, cursor_sqlite = db.connect_sqlite()
            move.start(
                connection_mysql=connection,
                cursor_mysql=cursor,
                connection_sqlite=connection_sqlite,
                cursor_sqlite=cursor_sqlite
            )
            db.close_sqlite(connection_sqlite)

        case "--stats":
            stats.start(
                connection=connection,
                cursor=cursor
            )

        case "--parseLoop":
            while True:
                parse.start(
                    connection=connection,
                    cursor=cursor
                )
                time.sleep(settings['loop_timeout'])

        case "--printLoop":
            while True:
                parse.start(
                    connection=connection,
                    cursor=cursor
                )
                cli.show(
                    connection=connection,
                    cursor=cursor
                )
                time.sleep(settings['loop_timeout'])

        case "--help":
            print("\nСписок аргументов для запуска программы:\n"
                  "1) --parse - Спарсить и сохранить данные\n"
                  "2) --print - Вывод последней записи в БД\n"
                  "3) --move - Перемещение данных с SqLite -> MySQL\n"
                  "4) --stats - Вывод графиков за 1 день\n"
                  "5) --parseLoop - Бесконечный парсинг\n"
                  "6) --printLoop - Бесконечный парсинг и вывод данных\n"
                  "7) --help - Вывод списка аргументов\n"
                  "8) NoneArgs - Запуск без аргументов\n")

        case "--noneArgs":
            start_loop(
                connection=connection,
                cursor=cursor,
                settings=settings
            )

        case _:
            print(f"--- Неверный аргумент запуска '{arg}'")


if __name__ == '__main__':
    start()

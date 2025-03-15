from gui import cli
from gui import stats
from parser import parse
from move import move
from database import database as db
import commentjson as json
import argparse
import time
import os


# Чтение глобальных настроек программы
def read_config():
    """
    Функция для считывания данных JSON с файла настроек с поддержкой комментариев
    :return: Словарь с конфигурационными данными
    """

    work_dir = os.getcwd()  # Текущая рабочая директория
    module = ""  # Имя поддиректории с модулем
    filename = "config.json"  # Имя конфига

    # Формируем абсолютный путь к config.json внутри модуля
    absolute_path = os.path.abspath(os.path.join(work_dir, module, filename))

    try:
        with open(absolute_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f'Ошибка чтения конфигурационного файла: {e}')
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
                 "7) /info - Вывести данную таблицу\n"\
                 "8) /exit - Выход из программы"
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

            case "/info":
                print(table_help)

            case "/exit":
                print("\n--- Выход из программы")
                exit(0)

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

    # Создаем группу взаимоисключающих аргументов
    group = parser.add_mutually_exclusive_group()

    # Добавляем каждый возможный аргумент как отдельный флаг
    group.add_argument('--parse', action='store_true', help='Run parsing mode')
    group.add_argument('--print', action='store_true', help='Run print mode')
    group.add_argument('--move', action='store_true', help='Run moving database SqLite to MySQL')
    group.add_argument('--stats', action='store_true', help='Run statistics mode')
    group.add_argument('--parseLoop', action='store_true', help='Run parsing loop')
    group.add_argument('--printLoop', action='store_true', help='Run parsing & print loop')
    group.add_argument('--info', action='store_true', help='Help table with command palette')

    # Обрабатываем поднятые флаги
    args = parser.parse_args()

    # Проверка на входные значения при запуске программы
    if args.parse:
        parse.start(
            connection=connection,
            cursor=cursor
        )
    if args.print:
        cli.show(
            connection=connection,
            cursor=cursor
        )
    if args.move:
        connection_sqlite, cursor_sqlite = db.connect_sqlite()
        move.start(
            connection_mysql=connection,
            cursor_mysql=cursor,
            connection_sqlite=connection_sqlite,
            cursor_sqlite=cursor_sqlite
        )
        db.close_sqlite(connection_sqlite)
    if args.stats:
        stats.start(
            connection=connection,
            cursor=cursor
        )
    if args.parseLoop:
        while True:
            parse.start(
                connection=connection,
                cursor=cursor
            )
            time.sleep(settings['loop_timeout'])
    if args.printLoop:
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
    if args.info:
        print("\nСписок аргументов для запуска программы:\n"
              "1) --parse - Спарсить и сохранить данные\n"
              "2) --print - Вывод последней записи в БД\n"
              "3) --move - Перемещение данных с SqLite -> MySQL\n"
              "4) --stats - Вывод графиков за 1 день\n"
              "5) --parseLoop - Бесконечный парсинг\n"
              "6) --printLoop - Бесконечный парсинг и вывод данных\n"
              "7) --help - Вывод списка аргументов\n"
              "8) NoneArgs - Запуск без аргументов\n")
    else:
        start_loop(
            connection=connection,
            cursor=cursor,
            settings=settings
        )


if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        print("\n\n--- Некорректный выход")
        exit(1)

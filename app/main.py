from gui import cli
from gui import graphs
import argparse  # Библиотека для работы с аргументами запуска
import threading  # Библиотека для работы с параллельным выполнением
import logging  # Библиотека для работы с логированием


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Функция запуска модулей через консоль
def run_console():
    table = ("Таблица команд:"
             "/print - Вывод таблицы данных\n"
             "/printLoop - Вывод таблицы данных в цикле\n"
             "/graphDay - Формирование графика за день\n"
             "/info - Вывод таблицы команд\n"
             "/exit - Выход из программы"
             )
    print(table)
    while True:
        command = str(input('Введите команду - '))
        match command:
            case '/print':
                cli.start()
            case '/printLoop':
                cli.start_loop()
            case '/graphDay':
                graphs.start_day(
                    time_start='2025-03-19-00-00',
                    time_end='2025-03-19-20-00'
                )
            case '/info':
                print(table)
            case '/exit':
                exit(0)
            case _:
                print(f"--- Неверная команда {command}")


# Функция запуска программы с аргументами
def start():
    # Функция запуска службы cli
    def run_show_mode():
        """
        Функция запуска парсинга в отдельном потоке
        :return: None
        """

        logger.info("Running show mode")
        cli.start()

    # Функция запуска службы cli в цикле
    def run_show_loop():
        """
        Функция запуска парсинга в отдельном потоке в режиме цикла
        :return: None
        """

        logger.info("Running parsing loop")
        cli.start_loop()

    # Функция запуска графа дня
    def run_graph_mode():
        """
        Функция запуска API-приложения
        :return: None
        """
        logger.info("Running graph mode")
        graphs.start_day(
            time_start='2025-03-19-00-00',
            time_end='2025-03-19-20-00'
        )

    # Функция работы в консольном виде
    def run_console_mode():
        logger.info("Running console mode")
        run_console()

    # Функция для вывода списка доступных аргументов запуска
    def show_info():
        logger.info("Help table with command palette")
        print("\nСписок аргументов для запуска программы:\n"
              "1) --parse - Спарсить и сохранить данные\n"
              "2) --parseLoop - Бесконечный парсинг\n"
              "3) --info - Вывод списка аргументов\n"
              )

    # Обработка входных команд при запуске
    parser = argparse.ArgumentParser(description="Process commands for Diabetes program")

    # Добавляем каждый возможный аргумент как отдельный флаг
    parser.add_argument('--print', action='store_true', help='Run show_cli mode')
    parser.add_argument('--printLoop', action='store_true', help='Run show_cli loop')
    parser.add_argument('--graphD', action="store_true", help='Run graph mode')
    parser.add_argument('--console', action="store_true", help='Run console mode')
    parser.add_argument('--info', action='store_true', help='Help table with command palette')

    # Обрабатываем поднятые флаги
    args = parser.parse_args()

    # Создаем список потоков
    threads = []

    # Проверка на входные значения при запуске программы
    if args.print:
        thread_parse = threading.Thread(target=run_show_mode)
        threads.append(thread_parse)
    if args.printLoop:
        thread_parse_loop = threading.Thread(target=run_show_loop)
        threads.append(thread_parse_loop)
    if args.graphD:
        thread_api = threading.Thread(target=run_graph_mode)
        threads.append(thread_api)
    if args.console:
        thread_console = threading.Thread(target=run_console_mode)
        threads.append(thread_console)
    if args.info:
        thread_info = threading.Thread(target=show_info)
        threads.append(thread_info)

    # Запускаем все потоки
    for thread in threads:
        thread.start()

    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        print("\n\n--- Некорректный выход")
        exit(1)

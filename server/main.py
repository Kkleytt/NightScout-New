from parser import parse  # Модуль для парсинга и сохранения данных
from database import database as db  # Модуль для работы с БД
from api import api  # Модуль для запуска API-сервера
import commentjson as json  # Библиотека для работы с JSON строками
import argparse  # Библиотека для работы с аргументами запуска
import time  # Библиотека для работы с временем
import os  # Библиотека для работы с файловой структурой
import threading  # Библиотека для работы с параллельным выполнением
import logging  # Библиотека для работы с логированием


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


# Функция запуска программы с аргументами
def start():
    # Функция для режима парсинга
    def run_parsing_mode():
        """
        Функция запуска парсинга в отдельном потоке
        :return: None
        """

        logger.info("Running parsing mode")
        parse.start()

    # Функция для режима парсинга в цикле
    def run_parsing_loop(loop_timeout):
        """
        Функция запуска парсинга в отдельном потоке в режиме цикла
        :param loop_timeout: Задержка между циклами
        :return: None
        """

        logger.info("Running parsing loop")
        while True:
            parse.start()
            time.sleep(loop_timeout)

    # Функция для запуска API
    def run_api_mode():
        """
        Функция запуска API-приложения
        :return: None
        """
        logger.info("Running API mode")
        api.start(connection=connection, cursor=cursor)

    # Функция для вывода справочной информации
    def show_info():
        logger.info("Help table with command palette")
        print("\nСписок аргументов для запуска программы:\n"
              "1) --parse - Спарсить и сохранить данные\n"
              "2) --parseLoop - Бесконечный парсинг\n"
              "3) --info - Вывод списка аргументов\n"
              )

    # Чтение настроек программы
    settings = read_config()

    # Подключение к БД (MySQL)
    connection, cursor = db.connect_mysql()
    if connection is None or cursor is None:
        exit(1001)

    # Обработка входных команд при запуске
    parser = argparse.ArgumentParser(description="Process commands for Diabetes program")

    # Добавляем каждый возможный аргумент как отдельный флаг
    parser.add_argument('--parse', action='store_true', help='Run parsing mode')
    parser.add_argument('--parseLoop', action='store_true', help='Run parsing loop')
    parser.add_argument('--api', action="store_true", help='Run API mode')
    parser.add_argument('--info', action='store_true', help='Help table with command palette')

    # Обрабатываем поднятые флаги
    args = parser.parse_args()

    # Создаем список потоков
    threads = []

    # Проверка на входные значения при запуске программы
    if args.parse:
        thread_parse = threading.Thread(target=run_parsing_mode)
        threads.append(thread_parse)
    if args.parseLoop:
        thread_parse_loop = threading.Thread(target=run_parsing_loop, args=(settings['loop_timeout']))
        threads.append(thread_parse_loop)
    if args.api:
        thread_api = threading.Thread(target=run_api_mode)
        threads.append(thread_api)
    if args.info:
        show_info()

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

from parser import parse  # Модуль для парсинга и сохранения данных
from api import api  # Модуль для запуска API-сервера
import argparse  # Библиотека для работы с аргументами запуска
import threading  # Библиотека для работы с параллельным выполнением
import logging  # Библиотека для работы с логированием
from time import sleep  # Библиотека для работы с задержкой
from reserve import reserve as res_db

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Функция запуска программы с аргументами
def start():
    # Функция для запуска API
    def run_api_mode():
        """
        Функция запуска API-приложения
        :return: None
        """
        logger.info("Running API mode")
        api.start()

    # Функция для режима парсинга
    def run_parsing_mode():
        """
        Функция запуска парсинга в отдельном потоке
        :return: None
        """

        logger.info("Running parsing mode")
        parse.start()

    # Функция для режима парсинга в цикле
    def run_parsing_loop():
        """
        Функция запуска парсинга в отдельном потоке в режиме цикла
        :return: None
        """

        logger.info("Running parsing loop")
        parse.start_loop()

    def reserve():
        logger.info("Running Reserver mode")
        res_db.start()

    # Функция для вывода справочной информации
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
    parser.add_argument('--parse', action='store_true', help='Run parsing mode')
    parser.add_argument('--parseLoop', action='store_true', help='Run parsing loop')
    parser.add_argument('--api', action="store_true", help='Run API mode')
    parser.add_argument('--reserve', action="store_true", help='Run move to reserve Database')
    parser.add_argument('--info', action='store_true', help='Help table with command palette')

    # Обрабатываем поднятые флаги
    args = parser.parse_args()

    # Создаем список потоков
    threads = []

    # Проверка на входные значения при запуске программы
    if args.api:
        thread_api = threading.Thread(target=run_api_mode)
        threads.append(thread_api)
    if args.parse:
        thread_parse = threading.Thread(target=run_parsing_mode)
        threads.append(thread_parse)
    if args.parseLoop:
        thread_parse_loop = threading.Thread(target=run_parsing_loop)
        threads.append(thread_parse_loop)
    if args.info:
        show_info()
    if args.reserve:
        reserve()

    # Запускаем все потоки
    for thread in threads:
        thread.start()
        sleep(2)

    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        print("\n\n--- Некорректный выход")
        exit(1)

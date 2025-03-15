import matplotlib.pyplot as plt
import numpy as np
import commentjson as json
import os
from database.database import send_request_db


# Функция чтения конфига в нужной директории
def read_config():
    """
    Функция для считывания данных JSON с файла настроек с поддержкой комментариев
    :return: Словарь с конфигурационными данными
    """

    work_dir = os.getcwd()  # Текущая рабочая директория
    module = "gui"  # Имя поддиректории с модулем
    filename = "config.json"  # Имя конфига

    # Формируем абсолютный путь к config.json внутри модуля
    absolute_path = os.path.abspath(os.path.join(work_dir, module, filename))

    try:
        with open(absolute_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f'Ошибка чтения конфигурационного файла: {e}')
        exit(101)


# Функция получения данных сахара за период
def get_data(connection, cursor, date_start, date_end):
    """
    Функция получение измерений сахара в промежутке дат
    :param connection: Объект подключения БД
    :param cursor: Объект курсора БД
    :param date_start: Дата начала поиска
    :param date_end: Дата конца поиска
    :return: Список измерений сахаров
    """

    query = "SELECT * FROM Sugar WHERE date BETWEEN %s AND %s"
    result = send_request_db(
        connection=connection,
        cursor=cursor,
        query=query,
        data=[date_start, date_end]
    )
    return result


# Функция подсчета промежутка времени
def check_time(first, end):
    """
    Функция подсчета промежутка часов
    :param first: Начальная дата
    :param end: Конечная дата
    :return: Список с минимальным и максимальным значением времени
    """

    return [int(first[1].split('-')[3]), int(end[1].split('-')[3]) + 1]


# Функция построения графа и вывода его на экран (ДЛЯ 1 ДНЯ)
def print_graph_day(data, time, theme, width, height):
    """
    Функция построения графика сахаров
    :param data: Список измерений сахаров
    :param time: Список часов для отображения
    :param theme: Выбранная тема
    :param width: Ширины графика
    :param height: Высота графика
    :return: None
    """

    try:
        x = np.linspace(time[0], time[1], len(data))
        y = [float(item[2]) for item in data]  # Использую float для точности

        # Создание графика
        fig, ax = plt.subplots(figsize=(width, height))

        # Настройка цветов
        ax.set_facecolor(theme['color1'])  # цвет фона
        plt.rcParams['text.color'] = theme['color2']  # Цвет текста
        plt.rcParams['axes.labelcolor'] = theme['color2']
        plt.rcParams['xtick.color'] = theme['color2']
        plt.rcParams['ytick.color'] = theme['color2']

        # Рисуем зоны цвета
        ax.axhspan(0, 4, facecolor='red', alpha=0.2)  # <4.0
        ax.axhspan(4, 5, facecolor='yellow', alpha=0.2)  # 4.0-5.0
        ax.axhspan(5, 7.5, facecolor='green', alpha=0.2)  # 5.0-7.5
        ax.axhspan(7.5, 10, facecolor='yellow', alpha=0.2)  # 7.5-10.0
        ax.axhspan(10, max(y) * 1.2, facecolor='red', alpha=0.2)  # >10.0

        # Соединяем точки линией
        ax.plot(
            x, y,
            color=theme['color3'],
            linestyle='--',
            alpha=1,
            label='Измеренные точки'
        )

        # Добавляем точки
        ax.scatter(
            x, y,
            color=theme['color3'],
            edgecolor=theme['color2'],
            s=30,
            zorder=3,
            label='Измеренные значения'
        )

        # Настройка оформления
        ax.set_xlabel('Время (часы)')
        ax.set_ylabel('Уровень сахара')
        ax.set_title('Динамика уровня сахара с цветовыми зонами', fontsize=14)
        ax.legend(
            facecolor=theme['color1'],
            edgecolor=theme['color2']
        )

        # Установка пределов оси X
        ax.set_xlim(time[0], time[1])  # Критически важно!
        ax.margins(x=0)  # Убираем отступы

        # Grid и сетка
        ax.grid(
            True,
            linestyle='--',
            alpha=0.3,
            color=theme['color3']
        )

        # Установка пределов оси Y с отступом
        ax.set_ylim(0, max(y) * 1.05)

        # Добавляем легенду для цветовых зон
        proxy = [
            plt.Rectangle((0, 0), 1, 1, fc='red', alpha=0.2),
            plt.Rectangle((0, 0), 1, 1, fc='yellow', alpha=0.2),
            plt.Rectangle((0, 0), 1, 1, fc='green', alpha=0.2),
            plt.Rectangle((0, 0), 1, 1, fc='yellow', alpha=0.2),
            plt.Rectangle((0, 0), 1, 1, fc='red', alpha=0.2)
        ]
        ax.legend(
            handles=proxy,
            labels=['<4.0', '4.0-5.0', '5.0-7.5', '7.5-10.0', '>10.0'],
            title='Зоны:',
            loc='upper left',
            bbox_to_anchor=(1, 1),
            facecolor=theme['color1'],
            edgecolor=theme['color3']
        )

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Ошибка построения графа - {e}")
        exit(501)


def start(connection, cursor):
    # Чтение настроек модуля
    data = read_config()

    # Получение измерений в диапазоне дат
    graphs_data = get_data(
        connection=connection,
        cursor=cursor,
        date_start='2025-03-09-12-00',
        date_end='2025-03-09-23-59'
    )

    time = check_time(graphs_data[0], graphs_data[-1])

    print_graph_day(
        data=graphs_data,
        time=time,
        theme=data['graphs']['themes'][data['graphs']['select_theme']],
        width=data['graphs']['width'],
        height=data['graphs']['height']
    )

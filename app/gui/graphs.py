import matplotlib.pyplot as plt  # Библиотека для визуализации данных (Версия 3.8.1)
import numpy as np  # Библиотека для анализа данных
import requests  # Библиотека для работы с HTTP запросами
import config as cfg
import datetime


# Функция получения токена
def auth_api() -> str | bool:
    """Функция для авторизации пользователя и получения JWT токена"""
    url = f"{cfg.API.url}/token"
    data = {"username": cfg.API.user_login, "password": cfg.API.user_password}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("Ошибка авторизации:", response.text)
        return False


# Функция построения графа и вывода его на экран (ДЛЯ 1 ДНЯ)
def start_day(time_start: str, time_end: str):
    """
    Функция вывода графика сахаров в промежутке дат
    :param time_start: Дата начала графика
    :param time_end: Дата окончания графика
    :return: График
    """

    # Получение токена для общения с API
    token = auth_api()
    if not token:
        print("Ошибка получения токена")
        return False

    # Получение данных сахаров
    headers = {"Authorization": f"Bearer {token}"}
    query_url = f"{cfg.API.url}/get/sugar/date/start={time_start}&end={time_end}"
    data = requests.get(query_url, headers=headers).json()
    if not data:
        print("Данные за данный временной промежуток отсутствуют")
        return False

    # Получение актуальной темы оформления графика
    theme = getattr(cfg.Graph.Themes, cfg.Graph.sel_theme)[0]

    # Построение списка оси x | y
    x = np.linspace(
        start=datetime.datetime.strptime(time_start, "%Y-%m-%d-%H-%M").hour,
        stop=datetime.datetime.strptime(time_end, "%Y-%m-%d-%H-%M").hour + 1,
        num=len(data)
    )
    y = [float(data[item]['sugar']) for item in data]

    # Создание графика
    fig, ax = plt.subplots(figsize=(
        cfg.Graph.width,
        cfg.Graph.height
    ))

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
        linewidths=0.5,
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
    ax.set_xlim(
        int(time_start.split('-')[3]),
        int(time_end.split('-')[3]) + 1
    )

    # Убираем отступы
    ax.margins(x=0)

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

    # Вывод графика на экран
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    start_day(
        time_start='2025-03-19-00-00',
        time_end='2025-03-19-20-00'
    )

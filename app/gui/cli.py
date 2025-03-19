from prettytable import PrettyTable  # Библиотека для вывода таблиц в консоль
import commentjson as json  # Библиотека для работы с JSON-строками
import os  # Библиотека для работы с файловой системы
import requests  # Библиотека для работы с HTTP запросами


LAST_PRINT_ID = None


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


# Функция вывода GUI-интерфейса в CLI-формате
def print_data(settings):
    """
    Функция вывода GUI-интерфейса в CLI-формате
    :param settings: JSON данные настроек модуля
    :return: None
    """

    def check_icon_sugar(sugar_result):
        """
        Функция применения иконки к показателю сахара
        :param sugar_result: Уровень сахара
        :return: icon
        """

        for range_str, icon in settings['cli']['sugar_levels'].items():
            try:
                # Разбиваем строку диапазона на low и high
                low_str, high_str = range_str.split('-')
                low = float(low_str.strip())
                high = float(high_str.strip())

                # Проверяем попадание значения в диапазон
                if low <= sugar_result <= high:
                    return icon
            except (ValueError, AttributeError):
                # Игнорируем некорректные диапазоны или значения
                continue
        return "❔"

    def check_icon_battery(level):
        """
        Функция применения иконки к показателю батареи и резервуара
        :param level: Параметр заряда (0-100)
        :return: icon
        """

        if int(level) > 30:
            return '🟩'
        elif 20 <= int(level) <= 30:
            return "🟨"
        elif int(level) <= 20:
            return '🟥'
        else:
            return '⬜'

    global LAST_PRINT_ID

    # Запросы для получения всех данных для построения GUI-интерфейса
    main_url = f"http://{settings['access']['api']['host']}:{settings['access']['api']['port']}"
    token = f"{settings['access']['api']['token']}"

    # Получение последней записи сахаров
    url = f"{main_url}/get/sugar/last/token={token}"
    data_sugar = requests.get(url=url).json()

    # Получение последней записи инсулина и еды
    url = f"{main_url}/get/insulin/last/token={token}"
    data_insulin = requests.get(url=url).json()

    # Получение последней записи устройств
    url = f"{main_url}/get/device/last/token={token}"
    data_device = requests.get(url=url).json()

    # Строка с датой и идентификатором записи
    date = f"{data_sugar['date']} " if settings['cli']['show']['date'] else ""
    id_record = f"{data_sugar['id']} " if settings['cli']['show']['id'] else ""

    # Остановка при выводе при совпадении с предыдущим выводом
    if id_record == LAST_PRINT_ID:
        return

    # Строка с уровнем глюкозы в крови (Показатель, цвет, тенденция, изменения)
    sugar_icon = f"{check_icon_sugar(round(float(data_sugar['sugar']), 1))}" if settings['cli']['show']['icons'] else ""
    sugar = f"{data_sugar['sugar']} " if settings['cli']['show']['sugar'] else ""
    tendency = f"{data_sugar['difference']} " if settings['cli']['show']['tendency'] else ""
    tendency_icon = ""
    if data_sugar['tendency'] == 'NOT COMPUTABLE' or data_sugar['tendency'] == '' and settings['cli']['show']['icons']:
        tendency_int = abs(float(data_sugar['difference']))
        if 0.3 >= tendency_int >= -0.3:
            tendency_icon = "➡️"
        elif 0.6 >= tendency_int > 0.3:
            tendency_icon = "↗️"
        elif 0.9 >= tendency_int > 0.6:
            tendency_icon = "⬆️️"
        elif tendency_int > 0.9:
            tendency_icon = "⬆️⬆️"
        elif -0.6 <= tendency_int < -0.3:
            tendency_icon = "↘️"
        elif -0.9 <= tendency_int < -0.6:
            tendency_icon = "⬇️"
        elif tendency_int < -0.9:
            tendency_icon = "⬇️"
    else:
        tendency_icon = f"{settings['cli']['tendency'][data_sugar['tendency']]} " if settings['cli']['show']['icons'] else ""

    # Генерация иконок
    battery_icon_pump = f"{check_icon_battery(data_device['pump_battery'])}" if settings['cli']['show']['icons'] else ""
    battery_icon_iaps = f"{check_icon_battery(data_device['phone_battery'])}" if settings['cli']['show']['icons'] else ""
    battery_icon_transmitter = f"{check_icon_battery(data_device['transmitter_battery'])}" if settings['cli']['show']['icons'] else ""
    cartridge_pump_icon = f"{check_icon_battery(data_device['pump_cartridge'] / 3)}" if settings['cli']['show']['icons'] else ""
    cartridge_icon = "🍶" if settings['cli']['show']['icons'] else ""

    # Генерация состояния устройств
    battery_pump = f"{data_device['pump_battery']}%" if settings['cli']['show']['battery'] else ""
    battery_iaps = f"{data_device['phone_battery']}%" if settings['cli']['show']['battery'] else ""
    battery_transmitter = f"{data_device['transmitter_battery']}%" if settings['cli']['show']['battery'] else ""
    cartridge_pump = f"{data_device['pump_cartridge']}U" if settings['cli']['show']['battery'] else ""
    phone_name = f"{data_device['phone_model']}"
    transmitter_name = f"{data_device['transmitter_model']}"
    pump_name = f"{data_device['pump_model']}"

    # Строка с последними событиями сделанными помпой
    if settings['cli']['show']['insulin']:
        injection_insulin = f"Injection {data_insulin['insulin']} " if data_insulin['insulin'] is not None else "Injection 0.0 "
        carbs_insulin = f"Carbs {data_insulin['carbs']} " if data_insulin['carbs'] is not None else "Carbs 0.0"
        duration_insulin = f"{data_insulin['duration']} min" if data_insulin['duration'] is not None else "0 min "
    else:
        injection_insulin = ""
        carbs_insulin = ""
        duration_insulin = ""

    # Создание автоматической таблицы, добавление данных, вывод таблицы в консоль
    table = PrettyTable()

    # Проверка на вывод компактной информации
    if settings['cli']['view_mode'] == 0:
        row_del = ["----------------------------", "----------------------------", "----------------------------"]
        row_0 = [f"{phone_name} {battery_icon_iaps} {battery_iaps}", date, id_record]
        row_1 = [f"{transmitter_name} {battery_icon_transmitter} {battery_transmitter}", injection_insulin, f"{sugar_icon} {sugar}"]
        row_2 = [f"{pump_name} {battery_icon_pump} {battery_pump}", carbs_insulin,
                 f"{tendency_icon}- {data_sugar['tendency']}"]
        row_3 = [f"{cartridge_icon}{cartridge_pump} {cartridge_pump_icon} {int(int(data_device['pump_cartridge']) / 3)}%",
                 duration_insulin, tendency]

        table.field_names = row_0
        table.add_row(row_1)
        table.add_row(row_del)
        table.add_row(row_2)
        table.add_row(row_del)
        table.add_row(row_3)

    elif settings['cli']['view_mode'] == 1:
        row_del = ["--------------------", "--------------------"]
        row_0 = ['Имя', 'Индикатор']
        row_1 = ['Уровень сахара', f"{sugar_icon} {sugar}{tendency_icon}"]
        row_2 = ['Кол-во инсулина', f"{cartridge_pump_icon} {int(int(data_device['pump_cartridge']) / 3)}%"]
        row_3 = ['Заряд помпы', f"{battery_icon_pump} {battery_pump}"]
        row_4 = ['Заряд трансмиттера', f"{battery_icon_transmitter} {battery_transmitter}"]
        row_5 = ['Заряд телефона', f"{battery_icon_iaps} {battery_iaps}"]
        row_6 = ['Дата обновления', f"{date}"]

        table.field_names = row_0
        table.add_row(row_1)
        table.add_row(row_del)
        table.add_row(row_2)
        table.add_row(row_del)
        table.add_row(row_3)
        table.add_row(row_del)
        table.add_row(row_4)
        table.add_row(row_del)
        table.add_row(row_5)
        table.add_row(row_del)
        table.add_row(row_6)

    elif settings['cli']['view_mode'] == 2:
        row_0 = ['Уровень сахара', 'Кол-во инсулина', 'Заряд батарей', 'Дата обновления данных']
        row_1 = [
            f"{sugar_icon} {sugar}{tendency_icon}",
            f"{cartridge_pump_icon} {int(int(data_device['pump_cartridge']) / 3)}%",
            f"{battery_icon_pump} {battery_pump}  >  "
            f"{battery_icon_transmitter} {battery_transmitter}  >  "
            f"{battery_icon_iaps} {battery_iaps}",
            f"{date}"
        ]

        table.field_names = row_0
        table.add_row(row_1)

    print("")
    print(table, "\n")

    LAST_PRINT_ID = id_record


# Функция вывода информации в консоль
def start():
    """
    Функция вывода информации в консоль
    :return: None
    """

    # Чтение настроек
    settings = read_config()

    # Вывод данных
    print_data(
        settings=settings
    )

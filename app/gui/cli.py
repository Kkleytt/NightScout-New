from prettytable import PrettyTable  # Библиотека для вывода таблиц в консоль
import time  # Библиотека для работы с временем
import json  # Библиотека для работы с JSON-строками
import os  # Библиотека для работы с файловой системы
from database.database import send_request_db  # Функция отправки запроса к БД


LAST_PRINT_ID = None


# Функция чтения конфига в нужной директории
def read_config():
    try:
        work_dir = os.getcwd()  # Текущая рабочая директория
        module = "gui"  # Имя поддиректории с модулем
        filename = "config.json"  # Имя конфига

        # Формируем абсолютный путь к config.json внутри модуля
        absolute_path = os.path.abspath(os.path.join(work_dir, module, filename))

        # Чтение данных и преобразование в JSON-объект
        with open(absolute_path, 'r') as f:
            data = json.load(f)

        return data
    except Exception as e:
        print(f'Ошибка чтения конфигурационного файла - {e}')
        return None


# Функция вывода GUI-интерфейса в CLI-формате
def print_data(connection, cursor, data):
    """
    Функция вывода GUI-интерфейса в CLI-формате
    :param connection: Объект соединения БД
    :param cursor: Объект курсора БД
    :param data: JSON данные настроек модуля
    :return: None
    """

    def check_icon_sugar(sugar_result):
        """
        Функция применения иконки к показателю сахара
        :param sugar_result: Уровень сахара
        :return: icon
        """

        for range_str, icon in data['cli']['sugar_levels'].items():
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
    query = "SELECT * FROM Sugar ORDER BY id DESC LIMIT 1"
    data_sugar = send_request_db(
        connection=connection,
        cursor=cursor,
        query=query
    )[0]

    query = "SELECT * FROM Insulin ORDER BY date DESC LIMIT 1"
    data_insulin = send_request_db(
        connection=connection,
        cursor=cursor,
        query=query
    )[0]

    query = "SELECT * FROM Device"
    data_device = send_request_db(
        connection=connection,
        cursor=cursor,
        query=query
    )[0]

    # Строка с датой и идентификатором записи
    date = f"{data_sugar[1]} " if data['cli']['show']['date'] else ""
    id_record = f"{data_sugar[0]} " if data['cli']['show']['id'] else ""

    # Остановка при выводе при совпадении с предыдущим выводом
    if id_record == LAST_PRINT_ID:
        return

    # Строка с уровнем глюкозы в крови (Показатель, цвет, тенденция, изменения)
    sugar_icon = f"{check_icon_sugar(round(float(data_sugar[2]), 1))} " if data['cli']['show']['icons']['sugar'] else ""
    sugar = f"{data_sugar[2]} " if data['cli']['show']['sugar'] else ""
    tendency = f"{data_sugar[4]} " if data['cli']['show']['tendency'] else ""
    tendency_icon = ""
    if data_sugar[3] == 'NOT COMPUTABLE' or data_sugar[3] == '' and data['cli']['show']['icons']['tendency']:
        tendency_int = abs(float(data_sugar[4]))
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
        tendency_icon = f"{data['cli']['tendency'][data_sugar[3]]} " if data['cli']['show']['icons']['tendency'] else ""

    # Строка с состоянием устройств (Заряд, объем, названия)
    battery_icon_pump = f"{check_icon_battery(data_device[4])} " if data['cli']['show']['icons']['battery'] else ""
    battery_icon_iaps = f"{check_icon_battery(data_device[2])} " if data['cli']['show']['icons']['battery'] else ""
    battery_icon_transmitter = f"{check_icon_battery(data_device[3])} " if data['cli']['show']['icons']['battery'] else ""
    cartridge_pump_icon = f"{check_icon_battery(data_device[5] / 3)}" if data['cli']['show']['icons']['battery'] else ""
    battery_pump = f"{data_device[4]}% " if data['cli']['show']['battery'] else ""
    battery_iaps = f"{data_device[2]}% " if data['cli']['show']['battery'] else ""
    battery_transmitter = f"{data_device[3]}% " if data['cli']['show']['battery'] else ""
    cartridge_pump = f"{data_device[5]}U " if data['cli']['show']['battery'] else ""
    phone_name = f"{data_device[10]}"
    transmitter_name = f"{data_device[11]}"
    pump_name = f"{data_device[9]}"

    # Строка с последними событиями сделанными помпой
    if data['cli']['show']['insulin']:
        base_insulin = f"Base {data_insulin[2]} " if data_insulin[2] is not None else "Base 0.00"
        injection_insulin = f"Injection {data_insulin[3]} " if data_insulin[3] is not None else "Injection 0.0"
        carbs_insulin = f"Carbs {data_insulin[4]} " if data_insulin[4] is not None else "Carbs 0.0"
        if data_insulin[5]:
            duration_insulin = f"{data_insulin[5]} min"
        else:
            duration_insulin = '0 min'
    else:
        base_insulin = ""
        injection_insulin = ""
        carbs_insulin = ""
        duration_insulin = ""

    # Создание автоматической таблицы, добавление данных, вывод таблицы в консоль
    table = PrettyTable()

    row_del = ["-------------------------", "-------------------------", "-------------------------"]
    row_0 = [data_device[1], f"{data_insulin[1]}.", date]
    row_1 = [f"{phone_name} {battery_icon_iaps}{battery_iaps}", base_insulin, f"{sugar_icon}{sugar}"]
    row_2 = [f"{transmitter_name} {battery_icon_transmitter}{battery_transmitter}", injection_insulin, f"{tendency_icon}-{data_sugar[3]}"]
    row_3 = [f"{pump_name} {battery_icon_pump}{battery_pump}", carbs_insulin, tendency]
    row_4 = [f"🍶 {cartridge_pump}{cartridge_pump_icon} {int(int(data_device[5]) / 3)}%", duration_insulin, id_record]

    table.field_names = row_0
    table.add_row(row_1)
    table.add_row(row_del)
    table.add_row(row_2)
    table.add_row(row_del)
    table.add_row(row_3)
    table.add_row(row_del)
    table.add_row(row_4)

    print("")
    print(table, "\n")

    LAST_PRINT_ID = id_record


# Функция вывода информации в консоль
def show(connection, cursor):
    """
    Функция вывода информации в консоль
    :param connection: Объект подключения к БД
    :param cursor: Объект курсора БД
    :return: None
    """

    # Чтение настроек
    data = read_config()

    # Вывод данных
    print_data(
        connection=connection,
        cursor=cursor,
        data=data
    )

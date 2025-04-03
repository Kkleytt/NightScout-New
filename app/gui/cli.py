from prettytable import PrettyTable  # Библиотека для вывода таблиц в консоль
import requests  # Библиотека для работы с HTTP запросами
import config as cfg
import datetime
from time import sleep


LAST_PRINT_ID = None


# Функция получения токена
def auth_api() -> str:
    """Функция для авторизации пользователя и получения JWT токена"""
    url = f"{cfg.API.url}/token"
    data = {"username": cfg.API.user_login, "password": cfg.API.user_password}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("Ошибка авторизации:", response.text)
        return "None"


# Функция получения данных с API
def parse_data(token: str):
    # Запросы для получения всех данных для построения GUI-интерфейса
    headers = {"Authorization": f"Bearer {token}"}

    # Получение последней записи сахаров
    url = f"{cfg.API.url}/get/sugar/last"
    sugar = requests.get(url=url, headers=headers).json()

    # Получение последней записи инсулина и еды
    url = f"{cfg.API.url}/get/insulin/last"
    insulin = requests.get(url=url, headers=headers).json()

    # Получение последней записи устройств
    url = f"{cfg.API.url}/get/device/last"
    device = requests.get(url=url, headers=headers).json()

    return sugar, insulin, device


# Функция для проверки корректности данных из БД
def check_data(data: dict, data_type: str) -> bool:
    """
    Функция для проверки корректности данных из БД.
    :param data: Словарь данных.
    :param data_type: Тип данных.
    :return: True, если данные корректны, иначе False.
    """
    # Определяем обязательные ключи для каждого типа данных
    required_keys = {
        "sugar": {"id", "date", "value", "tendency", "difference"},
        "insulin": {"id", "date", "value", "carbs", "duration", "type"},
        "device": {
            "id", "date", "phone_battery", "transmitter_battery", "pump_battery",
            "pump_cartridge", "cannula_date", "insulin_date", "sensor_date",
            "pump_name", "phone_name", "transmitter_name", "insulin_name", "sensor_name"
        }
    }

    # Проверяем, что переданный тип данных поддерживается
    if data_type not in required_keys:
        print(f"Неизвестный тип данных: {data_type}")
        return False

    # Получаем множество обязательных ключей для указанного типа данных
    keys_to_check = required_keys[data_type]

    # Проверяем, что все обязательные ключи присутствуют в данных
    missing_keys = keys_to_check - data.keys()
    if missing_keys:
        print(f"Не хватает данных в списке {data_type}: {missing_keys}")
        return False

    return True


# Функция вывода GUI-интерфейса в CLI-формате
def print_data(data_sugar: dict, data_insulin: dict, data_device: dict):
    """
    Функция для вывода информации в виде CLI таблиц
    :param data_sugar: Данные о сахаре
    :param data_insulin: Данные об инсулине и еде
    :param data_device: Данные об устройствах
    :return: None
    """

    def check_icon_sugar(sugar_result: float) -> str:
        """
        Функция применения иконки к показателю сахара
        :param sugar_result: Уровень сахара
        :return: icon
        """

        for range_str, icon in cfg.ClI.Levels.sugar_1.items():
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

    def check_icon_battery(level: int) -> str:
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

    def unix_to_datetime(unix_date: int, date_format: str) -> str:
        """
        Функция для перевода UNIX даты в строку по переданному образцу
        :param unix_date: UNIX дата (в секундах)
        :param date_format: Строка с выражением Datetime для оформления даты
        :return: Строка с временем
        """
        try:
            # Преобразуем UNIX timestamp в объект datetime
            dt = datetime.datetime.fromtimestamp(unix_date)

            # Форматируем дату в указанный формат
            formatted_date = dt.strftime(date_format)

            return f"{formatted_date} "
        except (TypeError, ValueError) as e:
            raise ValueError(f"Ошибка преобразования: {e}") from e

    global LAST_PRINT_ID

    # Строка с датой и идентификатором записи
    date = unix_to_datetime(
        unix_date=data_sugar['date'],
        date_format=cfg.ClI.date_format
    ) if cfg.ClI.Show.date else ""
    id_record = f"{data_sugar['id']} " if cfg.ClI.Show.id else ""

    # Остановка при выводе при совпадении с предыдущим выводом
    if id_record == LAST_PRINT_ID:
        return

    # Строка с уровнем глюкозы в крови (Показатель, цвет, тенденция, изменения)
    sugar_value = round(float(data_sugar['value'] / 18), 1) if cfg.ClI.convert_to_mmol else data_sugar['value']
    sugar_icon = check_icon_sugar(sugar_value) if cfg.ClI.Show.icons else ""
    sugar = f"{sugar_value} " if cfg.ClI.Show.sugar else ""
    if data_sugar['tendency'] == 'NOT COMPUTABLE' or data_sugar['tendency'] == '' and cfg.ClI.Show.tendency:
        tendency_float = float(data_sugar['difference'] // 18) if cfg.ClI.convert_to_mmol else float(data_sugar['difference'])
        tendency_int = abs(tendency_float)
        if 0.3 >= tendency_int >= -0.3:
            tendency = "Flat"
        elif 0.6 >= tendency_int > 0.3:
            tendency = "FortyFiveUp"
        elif 0.9 >= tendency_int > 0.6:
            tendency = "SingleUp️"
        elif tendency_int > 0.9:
            tendency = "DoubleUp"
        elif -0.6 <= tendency_int < -0.3:
            tendency = "FortyFiveDown"
        elif -0.9 <= tendency_int < -0.6:
            tendency = "SingleDown"
        elif tendency_int < -0.9:
            tendency = "DoubleDown"
        else:
            tendency = "Flat"
    else:
        tendency = data_sugar['tendency']

    tendency_icon = f"{cfg.ClI.tendency[tendency]} " if cfg.ClI.Show.icons else ""

    # Генерация иконок
    cartridge_pump_percent = int(data_device['pump_cartridge']) // 3
    if cfg.ClI.Show.icons:  # Проверка на отображение иконок
        battery_icon_pump = check_icon_battery(data_device['pump_battery'])
        battery_icon_iaps = check_icon_battery(data_device['phone_battery'])
        battery_icon_transmitter = check_icon_battery(data_device['transmitter_battery'])
        cartridge_pump_icon = check_icon_battery(cartridge_pump_percent)
        cartridge_icon = "🍶"
    else:
        battery_icon_pump = ""
        battery_icon_iaps = ""
        battery_icon_transmitter = ""
        cartridge_pump_icon = ""
        cartridge_icon = ""

    # Генерация состояния устройств
    if cfg.ClI.Show.battery:  # Проверка на отображение состояний батарей
        battery_pump = f"{data_device['pump_battery']}%"
        battery_iaps = f"{data_device['phone_battery']}%"
        battery_transmitter = f"{data_device['transmitter_battery']}%"
        cartridge_pump = f"{data_device['pump_cartridge']}U"
    else:
        battery_pump = ""
        battery_iaps = ""
        battery_transmitter = ""
        cartridge_pump = ""
    phone_name = data_device['phone_name']
    transmitter_name = data_device['transmitter_name']
    pump_name = data_device['pump_name']
    insulin_name = data_device['insulin_name']
    sensor_name = data_device['sensor_name']

    # Строка с последними событиями сделанными помпой
    if cfg.ClI.Show.insulin:
        injection_insulin = f"{insulin_name} {data_insulin['value']}"
        carbs_insulin = f"Carbs {data_insulin['carbs']}"
        duration_insulin = f"{data_insulin['duration']} min"
    else:
        injection_insulin = ""
        carbs_insulin = ""
        duration_insulin = ""

    # Создание автоматической таблицы, добавление данных, вывод таблицы в консоль
    table = PrettyTable()

    # Проверка на вид отображаемой таблицы
    match cfg.ClI.view_mode:
        case 0:
            row_del = ["----------------------------", "----------------------------", "----------------------------"]
            row_0 = [
                f"{phone_name} {battery_icon_iaps} {battery_iaps}",
                date,
                id_record
            ]
            row_1 = [
                f"{transmitter_name} {battery_icon_transmitter} {battery_transmitter}",
                injection_insulin,
                f"{sugar_icon} {sugar}"
            ]
            row_2 = [
                f"{pump_name} {battery_icon_pump} {battery_pump}",
                carbs_insulin,
                f"{tendency_icon}- {data_sugar['tendency']}"
            ]
            row_3 = [
                f"{cartridge_icon}{cartridge_pump} {cartridge_pump_icon} {cartridge_pump_percent}%",
                duration_insulin,
                sensor_name
            ]

            table.field_names = row_0
            table.add_row(row_1)
            table.add_row(row_del)
            table.add_row(row_2)
            table.add_row(row_del)
            table.add_row(row_3)
        case 1:
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
        case 2:
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

    print("\n", table, end="\n")

    LAST_PRINT_ID = id_record


# Функция вывода информации в консоль
def start():
    """
    Функция вывода информации в консоль
    :return: None
    """
    # Получение токена для общения с API
    api_token = auth_api()

    # Проверка на полученный токен
    if api_token == "None":
        print("Ошибка получения токена")
        return False

    # Сбор данных с API
    sugar, insulin, device = parse_data(token=api_token)

    # Вывод данных
    print_data(
        data_sugar=sugar,
        data_insulin=insulin,
        data_device=device
    )


def start_loop():
    """
    Функция цикличного вывода информации в консоль
    :return: None
    """

    # Получение токена для общения с API
    api_token = auth_api()
    token_creation_time = datetime.datetime.now()

    # Проверка на полученный токен
    if api_token == "None":
        print("Ошибка получения токена")
        return False

    while True:
        try:
            # Проверка, истёк ли срок действия токена
            if datetime.datetime.now() >= token_creation_time + datetime.timedelta(minutes=cfg.API.life_token):
                api_token = auth_api()
                if api_token == "None":
                    return False
                token_creation_time = datetime.datetime.now()

            # Сбор данных с API
            sugar, insulin, device = parse_data(token=api_token)

            # Проверка данных
            sugar_status = check_data(sugar, "sugar")
            insulin_status = check_data(insulin, "insulin")
            device_status = check_data(device, "device")

            # Проверка на отсутствие ошибок в данных
            if sugar_status and insulin_status and device_status:
                # Вывод данных
                print_data(
                    data_sugar=sugar,
                    data_insulin=insulin,
                    data_device=device
                )
        except Exception as e:
            print(f"Неизвестная ошибка в модуле CLI - {e}")

        # Задержка циклов
        sleep(cfg.Loop.timeout)


if __name__ == '__main__':
    start_loop()

from database.database import MySQL
import requests
from datetime import datetime
import config as cfg


# Класс отвечающий за редактирование данных
class EditData:
    # Функция конвертации времени в unix формат
    @staticmethod
    def date_to_unix(date_str: str) -> int:
        return int(datetime.strptime(date_str, "%Y-%m-%d-%H-%M").timestamp())

    # Функция конвертации идентификатора (xxxx:xxxx:xxxx) в число
    @staticmethod
    def id_to_int(str_id: str) -> int:
        data = str_id.split(":")
        return int(f"{data[0]}{data[1]}{data[2]}")

    # Функция конвертации разницы сахара в число
    @staticmethod
    def difference_to_float(str_diff: str) -> float:
        return float(str_diff)

    # Функция изменения данных сахара
    def sugars(self, old_data: list) -> list:
        """
        Список переменных для выравнивания (изменения) данных под новую БД
        sugar_data - Изначальный список со старой БД
        sugar_data_change_1 - Список с измененными датами (строка -> unix-формат (часовой пояс - 0))
        sugar_data_change_2 - Список с измененными id (строка -> int)
        sugar_data_change_3 - Список с измененными difference (строка -> float)
        sugar_data_change_4 - Список с измененными значениями сахара (mmol/литр -> грамм/литр)

        Необходимые изменения в БД:
        id (str -> int)
        date (str -> int)
        difference (str -> float)
        sugar -> value
        """

        print("Данные сахара:")
        print(f"\tСтарые - {old_data}")

        # Перевод дат в UNIX формат
        sugar_data_change_1 = []
        for item in old_data:
            sugar_data_change_1.append([item[0], self.date_to_unix(item[1]), item[2], item[3], item[4]])

        # Перевод ID в INT-формат
        sugar_data_change_2 = []
        for item in sugar_data_change_1:
            sugar_data_change_2.append([self.id_to_int(item[0]), item[1], item[2], item[3], item[4]])

        # Перевод Difference в INT-формат
        sugar_data_change_3 = []
        for item in sugar_data_change_2:
            sugar_data_change_3.append([item[0], item[1], item[2], item[3], self.difference_to_float(item[4])])

        # Перевод сахаров в формат грамм/литр
        sugar_data_change_4 = []
        for item in sugar_data_change_3:
            sugar_data_change_4.append([item[0], item[1], (item[2] * 8), item[3], item[4]])

        print(f"\tНовые данные - {sugar_data_change_4}")
        return sugar_data_change_4

    # Функция изменения данных инсулина
    def insulin(self, old_data: list) -> list:
        """
        Список переменных для выравнивания (изменения) данных под новую БД
        insulin_data - Изначальный список со старой БД
        insulin_data_change_1 - Список с измененными датами (строка -> unix-формат (часовой пояс - 0))
        insulin_data_change_2 - Список с измененными id (строка -> int)

        Необходимые изменения в БД:
        id (str -> int)
        date (str -> int)
        carbs (int -> float)
        insulin -> value
        """

        print("Данные инсулина:")
        print(f"\tСтарые - {old_data}")

        # Перевод дат в UNIX формат
        insulin_data_change_1 = []
        for item in old_data:
            insulin_data_change_1.append(
                [item[0], self.date_to_unix(item[1]), item[2], item[3], item[4], item[5]]
            )

        # Перевод ID в INT-формат
        insulin_data_change_2 = []
        for item in insulin_data_change_1:
            insulin_data_change_2.append(
                [self.id_to_int(item[0]), item[1], item[2], item[3], item[4], item[5]]
            )

        print(f"\tНовые - {insulin_data_change_2}")
        return insulin_data_change_2

    # Функция изменения данных устройств
    def device(self, old_data: list) -> list:
        """
        Список переменных для выравнивания (изменения) данных под новую БД
        device_data - Изначальный список со старой БД
        device_data_change_1 - Список с измененными датами (строка -> unix-формат (часовой пояс - 0))

        Необходимые изменения в БД:
        (FORMAT) date (str -> int)
        (FORMAT) cannula (str -> int)
        (FORMAT) insulin (str -> int)
        (FORMAT) sensor (str -> int)

        (RENAME) phone_model -> phone_name
        (RENAME) transmitter_model -> transmitter_name
        (RENAME) pump_model -> pump_name
        (RENAME) cannula -> cannula_date
        (RENAME) insulin -> insulin_date
        (RENAME) sensor -> sensor_date

        (ADD) insulin_name (str)
        (ADD) sensor_name (str)
        """

        print("Данные устройств:")
        print(f"\tСтарые - {old_data}")

        # Конвертация даты в UNIX формат
        device_data_change_1 = [
            old_data[0], self.date_to_unix(old_data[1]),  # ID & Date
            old_data[2], old_data[3], old_data[4], old_data[5],  # Phone_battery & Transmitter_battery & Pump_battery & Pump_cartridge
            old_data[6], old_data[7], old_data[8],  # Cannula & Sensor & Insulin
            old_data[9], old_data[10], old_data[11]  # Pump_model & Transmitter_model & Phone_model
        ]

        # Добавление пустых данных в список
        """
        Структура старого списка:
        [0] - Id, 
        [1] - Date, 
        [2] - Phone_battery,
        [3] - Transmitter_battery, 
        [4] - Pump_battery, 
        [5] - Pump_cartridge,
        [6] - Cannula, 
        [7] - Sensor, 
        [8] - Insulin,
        [9] - Pump_model,  
        [10] - Phone_model,
        [11] - Transmitter_model

        Структура нового списка:
        [0] - id (INT)
        [1] - date (INT)

        [2] - phone_battery (INT)
        [3] - transmitter_battery (INT) 
        [4] - pump_battery (INT)
        [5] - pump_cartridge (INT)

        [6] - cannula_date (INT)
        [7] - sensor_date (INT)
        [8] - insulin_date (INT)

        [9] - pump_name (STR)
        [10] - phone_name (STR)
        [11] - transmitter_name (STR)
        [12] - insulin_name (STR)
        [13] - sensor_name (STR)
        """
        device_data_change_2 = [
            device_data_change_1[0],
            device_data_change_1[1],

            device_data_change_1[2],
            device_data_change_1[3],
            device_data_change_1[4],
            device_data_change_1[5],

            device_data_change_1[6],
            device_data_change_1[7],
            device_data_change_1[8],

            device_data_change_1[9],
            device_data_change_1[10],
            device_data_change_1[11],
            "Fiasp",
            "FreeStyle Libre 1"
        ]

        print(f"\tНовые - {device_data_change_2}")
        return device_data_change_2


# Аутентификация в API
def auth_api():
    """Функция для авторизации пользователя и получения JWT токена"""
    url = f"{cfg.Parser.API.main_url}/token"
    data = {"username": cfg.Parser.API.user_login, "password": cfg.Parser.API.user_password}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("Ошибка авторизации:", response.text)
        return False


# Получение данных из основной БД путем API-запросов
def get_data_from_api(query, params, token):
    json_data = {
        'query': query,
        'params': params
    }
    main_url = cfg.Parser.API.main_url
    headers = {"Authorization": f"Bearer {token}"}

    url = f"{main_url}/put/command"
    data = requests.put(url=url, json=json_data, headers=headers).json()
    return data


# Получение новых данных на основе старых записей
def get_new_data(count=0, sugar=True, insulin=True, device=True):
    # Получение токена API-сервера
    api_token = auth_api()

    edit_manager = EditData()

    if sugar:
        # Получение данных Сахаров
        old_data = get_data_from_api(
            query=f"SELECT * FROM Sugar ORDER BY id DESC LIMIT {count}",
            params=[],
            token=api_token
        )

        # Изменения данных Сахаров
        sugar_data = edit_manager.sugars(old_data=old_data)
    else:
        sugar_data = None

    if insulin:
        # Получение данных Инсулина
        old_data = get_data_from_api(
            query=f"SELECT * FROM Insulin ORDER BY id DESC LIMIT {count}",
            params=[],
            token=api_token
        )

        # Изменения данных Инсулина
        insulin_data = edit_manager.insulin(old_data=old_data)
    else:
        insulin_data = None

    if device:
        # Получение данных Устройств
        old_data = get_data_from_api(
            query=f"SELECT * FROM Device",
            params=[],
            token=api_token
        )[0]

        # Изменения данных Устройств
        device_data = edit_manager.device(old_data=old_data)
    else:
        device_data = None

    return {
        "sugar": sugar_data,
        "insulin": insulin_data,
        "device": device_data
    }


# Универсальный старт модуля
def start(count=10, sugar=True, insulin=True, device=True):
    if count <= 0:
        print("Кол-во данных меньше или равно 0")
        return 0

    # Подключение к Резервной Базе Данных
    reserve_db = MySQL(
        host=cfg.DatabaseReserve.host,
        port=cfg.DatabaseReserve.port,
        user=eval(f"cfg.DatabaseReserve.{cfg.DatabaseReserve.sel_user}.login"),
        password=eval(f"cfg.DatabaseReserve.{cfg.DatabaseReserve.sel_user}.password"),
        database=cfg.DatabaseReserve.database,
        retry_max=cfg.DatabaseReserve.retry_max,
        retry_delay=cfg.DatabaseReserve.retry_delay,
        timeout=cfg.DatabaseReserve.timeout,
        read_timeout=cfg.DatabaseReserve.read_timeout,
        write_timeout=cfg.DatabaseReserve.write_timeout
    )

    # Получение данных из БД + выравнивание данных
    new_data = get_new_data(
        count=count,
        sugar=sugar,
        insulin=insulin,
        device=device
    )

    permission = input(f"\n\nСогласны выполнить запись новых данных в резервную БД ?\n"
                       f"\tIP - {cfg.DatabaseReserve.host}:{cfg.DatabaseReserve.port}\n"
                       f"\tUser - {eval(f"cfg.DatabaseReserve.{cfg.DatabaseReserve.sel_user}.login")}\n"
                       f"Кол-во новых данных для записи:\n"
                       f"\tСахаров - {len(new_data['sugar'])}\n"
                       f"\tИнсулина - {len(new_data['insulin'])}\n"
                       f"\tУстройств - 1\n\n"
                       f"Записать данные? (YES / NO) - ").upper()
    if permission == "NO" or permission == "N":
        print("Отказ от записи данных в резервную БД")
    elif permission == "YES" or permission == "Y":
        print("Начата запись новых объектов в БД")
    else:
        print("Некорректный ввод")

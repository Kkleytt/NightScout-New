from database.database import MySQL
import requests
from datetime import datetime
import config as cfg


class ReserveDB(MySQL):
    def reset_tables(self, sugar: bool, insulin: bool, device: bool) -> None:
        """
        Функция удаления таблиц (Сброса БД)
        :param sugar: Сброс таблицы Sugar
        :param insulin: Сброс таблицы Insulin
        :param device: Сброс таблицы Device
        :return: None
        """

        if sugar:
            query = "DROP TABLE Sugar"
            self.execute_query(query=query, params=[])
        if insulin:
            query = "DROP TABLE Insulin"
            self.execute_query(query=query, params=[])
        if device:
            query = "DROP TABLE Device"
            self.execute_query(query=query, params=[])

    def create_table(self, sugar: bool, insulin: bool, device: bool) -> None:
        """
        Функция создания новых таблиц в БД
        :param sugar: Создание таблицы Sugar
        :param insulin: Создание таблицы Insulin
        :param device: Создание таблицы Device
        :return: None
        """

        if sugar:
            query = """CREATE TABLE Sugar (
            id INT,
            date INT,
            value FLOAT,
            tendency TEXT,
            difference FLOAT
            )"""
            self.execute_query(query=query, params=[])
        if insulin:
            query = """CREATE TABLE Insulin (
            id INT,
            date INT,
            value FLOAT,
            carbs INT,
            duration INT,
            type TEXT
            )"""
            self.execute_query(query=query, params=[])
        if device:
            query = """CREATE TABLE Device (
            id INT,
            date INT,
            phone_battery INT,
            transmitter_battery INT,
            pump_battery INT,
            pump_cartridge INT,
            insulin_date INT,
            cannula_date INT,
            sensor_date INT,
            pump_name TEXT,
            phone_name TEXT,
            transmitter_name TEXT,
            insulin_name TEXT,
            sensor_name TEXT
            )"""
            self.execute_query(query=query, params=[])

    def add_sugar(self, data: list) -> None:
        """
        Функция записи данных сахаров
        :param data: Список данных новой строки
        :return: None
        """

        query = f"INSERT INTO {self.database}.Sugar VALUES (%s, %s, %s, %s, %s)"
        self.execute_query(query=query, params=data)

    def add_insulin(self, data) -> None:
        """
        Функция записи данных инсулина
        :param data: Список данных новой строки
        :return: None
        """

        query = f"INSERT INTO {self.database}.Insulin VALUES (%s, %s, %s, %s, %s, %s)"
        self.execute_query(query=query, params=data)

    def add_device(self, data) -> None:
        """
        Функция записи данных устройств
        :param data: Список данных новой строки
        :return: None
        """

        query = f"INSERT INTO {self.database}.Device VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.execute_query(query=query, params=data)


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
        sugar_data_change_5 - Список с откорректированными значениями разницы между сахарами

        Необходимые изменения в БД:
        id (str -> int)
        date (str -> int)
        difference (str -> float)
        sugar -> value
        """

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
            sugar_data_change_4.append([item[0], item[1], int(item[2] * 18), item[3], item[4]])

        # Перевод разницы между сахарами в формат грамм/литр
        sugar_data_change_5 = []
        for item in sugar_data_change_4:
            sugar_data_change_5.append([item[0], item[1], item[2], item[3], round(item[4] * 18, 0)])

        return sugar_data_change_5

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
        insulin -> value
        """

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

        return insulin_data_change_2

    # Функция изменения данных устройств
    def device(self, old_data: list) -> list:
        """
        Список переменных для выравнивания (изменения) данных под новую БД
        device_data - Изначальный список со старой БД
        device_data_change_1 - Список с измененными датами (строка -> unix-формат (часовой пояс - 0))
        device_data_change_2 - Список с актуальным временем в полях sensor, insulin, cannula

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

        # Конвертация даты в UNIX формат
        device_data_change_1 = [
            old_data[0], self.date_to_unix(old_data[1]),  # ID & Date
            old_data[2], old_data[3], old_data[4], old_data[5],  # Phone_battery & Transmitter_battery & Pump_battery & Pump_cartridge
            old_data[6], old_data[7], old_data[8],  # Cannula & Sensor & Insulin
            old_data[9], old_data[10], old_data[11]  # Pump_model & Transmitter_model & Phone_model
        ]

        # Добавление новых данных в список
        """
        Структура нового списка:
        [0] - id (INT)                          [7] - sensor_date (INT)
        [1] - date (INT)                        [8] - insulin_date (INT)
        [2] - phone_battery (INT)               [9] - pump_name (STR)
        [3] - transmitter_battery (INT)         [10]- phone_name (STR)
        [4] - pump_battery (INT)                [11]- transmitter_name (STR)
        [5] - pump_cartridge (INT)              [12]- insulin_name (STR)
        [6] - cannula_date (INT)                [13]- sensor_name (STR)        
        """
        device_data_change_2 = [
            device_data_change_1[0],
            device_data_change_1[1],

            device_data_change_1[2],
            device_data_change_1[3],
            device_data_change_1[4],
            device_data_change_1[5],

            int(datetime.now().timestamp()),
            int(datetime.now().timestamp()),
            int(datetime.now().timestamp()),

            device_data_change_1[9],
            device_data_change_1[10],
            device_data_change_1[11],
            "Fiasp",
            "FreeStyle Libre 1"
        ]

        return device_data_change_2


# Класс отвечающий за получение данных
class GetData:
    def __init__(self):
        self.api_url = cfg.Parser.API.main_url
        self.api_username = cfg.Parser.API.user_login
        self.api_password = cfg.Parser.API.user_password
        self.api_token = self.auth_api()
        self.headers = {"Authorization": f"Bearer {self.api_token}"}

    def auth_api(self) -> str | bool:
        """Функция для авторизации пользователя и получения JWT токена"""
        url = f"{self.api_url}/token"
        data = {"username": self.api_username, "password": self.api_password}
        response = requests.post(url, json=data)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print("Ошибка авторизации:", response.text)
            return False

    def get_data_from_api(self, query: str, params: list) -> list:
        """
        Получение данных через запрос к API
        :param query: SQL-запрос передаваемый через HTTP
        :param params: Параметры запроса
        :return:
        """
        json_data = {
            'query': query,
            'params': params
        }
        url = f"{self.api_url}/put/command"
        data = requests.put(url=url, json=json_data, headers=self.headers).json()
        return data

    def get_sugar_data(self, count: int) -> list:
        return self.get_data_from_api(
            query=f"SELECT * FROM Sugar ORDER BY id DESC LIMIT {count}",
            params=[]
        )

    def get_insulin_data(self, count: int) -> list:
        return self.get_data_from_api(
            query=f"SELECT * FROM Insulin ORDER BY id DESC LIMIT {count}",
            params=[]
        )

    def get_device_data(self) -> list:
        return self.get_data_from_api(
            query="SELECT * FROM Device",
            params=[]
        )[0]


def show_old_and_new_data(old_json_data: dict, new_json_data: dict) -> None:
    """
    Функция для вывода сравнительной таблицы старых и новых данных
    :param old_json_data: JSON строка старых данных
    :param new_json_data: JSON строка новых данных
    :return: None
    """

    print("Сравнительная таблица")
    if old_json_data['sugar'] is not None:
        print(f"Таблица 'Sugar':\n"
              f"\tНачальные данные - {old_json_data['sugar']}\n"
              f"\tИзмененные данные - {new_json_data['sugar']}")

    if old_json_data['insulin'] is not None:
        print(f"Таблица 'Insulin':\n"
              f"\tНачальные данные - {old_json_data['insulin']}\n"
              f"\tИзмененные данные - {new_json_data['insulin']}")

    if old_json_data['device'] is not None:
        print(f"Таблица 'Device':\n"
              f"\tНачальные данные - {old_json_data['device']}\n"
              f"\tИзмененные данные - {new_json_data['device']}")

    print("\n\n")


# Универсальный старт модуля
def start(count=40000, sugar=True, insulin=True, device=True, edit_mode=False, save_mode=True, reset_db=True, create_db=True):
    """
    Универсальная функция переноса данных в Резервную БД
    :param count: Кол-во переносимых данных из таблицы sugar и insulin
    :param sugar: Перенос сахара
    :param insulin: Переноса инсулина и еды
    :param device: Перенос устройств
    :param edit_mode: Изменение данных после получения
    :param save_mode: Сохранение данных после получения
    :param reset_db: Сброс БД перед записью новых данных
    :param create_db: Создание новых таблиц
    :return: None
    """

    # Остановка функции при неверных аргументах
    if count <= 0:
        print("Кол-во данных меньше или равно 0")
        return 0

    # Получение изначальных данных
    data_manager = GetData() if sugar or insulin or device else None
    sugar_data = data_manager.get_sugar_data(count=count) if sugar else None
    insulin_data = data_manager.get_insulin_data(count=count) if insulin else None
    device_data = data_manager.get_device_data() if device else None

    # Изменение данных под новые стандарты
    edit_manager = EditData() if edit_mode else None
    new_sugar_data = edit_manager.sugars(old_data=sugar_data) if sugar and edit_mode else None
    new_insulin_data = edit_manager.insulin(old_data=insulin_data) if insulin and edit_mode else None
    new_device_data = edit_manager.device(old_data=device_data) if device and edit_mode else None

    # Вывод сравнительных данных
    show_old_and_new_data(
        old_json_data={
            "sugar": sugar_data,
            "insulin": insulin_data,
            "device": device_data
        },
        new_json_data={
            "sugar": new_sugar_data,
            "insulin": new_insulin_data,
            "device": new_device_data
        }
    )

    # Подключение к Резервной БД (MySQL)
    reserve_db = ReserveDB(
        host=cfg.Reserve.Database.host,
        port=cfg.Reserve.Database.port,
        user=eval(f"cfg.Reserve.Database.{cfg.Reserve.Database.sel_user}.login"),
        password=eval(f"cfg.Reserve.Database.{cfg.Reserve.Database.sel_user}.password"),
        database=cfg.Reserve.Database.database,
        retry_max=cfg.Reserve.Database.retry_max,
        retry_delay=cfg.Reserve.Database.retry_delay,
        timeout=cfg.Reserve.Database.timeout,
        read_timeout=cfg.Reserve.Database.read_timeout,
        write_timeout=cfg.Reserve.Database.write_timeout
    )

    # Проверка на согласие удалять таблицы
    test = str(input("Хотите начать процесс сброса таблиц? (YES/NO) - ")).upper()
    if test == "YES" or test == "Y":
        # Удаление таблиц
        reserve_db.reset_tables(
            sugar=sugar,
            insulin=insulin,
            device=device
        ) if reset_db else None

        # Создание новых таблиц
        reserve_db.create_table(
            sugar=sugar,
            insulin=insulin,
            device=device
        ) if create_db else None

    # Процесс записи данных
    if save_mode:
        # Первичный запрос для записи данных в резервную БД
        test = str(input("Хотите начать процесс записи данных? (YES/NO) - ")).upper()

        # Проверка первичного запроса
        if test == "NO" or test == "N":
            print("\t" + "Запись данных в Резервную БД - ОТМЕНЕНА")
            return
        elif test == "YES" or test == "Y":
            print("")
        else:
            print("\t" + "Некорректный ввод")
            print("\t" + "Запись данных в Резервную БД - ОТМЕНЕНА")
            return

        # Запись данных сахара
        if sugar:
            # Получение финальных данных
            sugar_write = new_sugar_data if edit_mode else sugar_data

            # Финальный вопрос перед записью данных
            final_test = str(input("Записать данные сахаров в Резервную БД? (YES/NO) - ")).upper()
            if final_test == "YES" or final_test == "Y":
                for item in reversed(sugar_write):  # Перебор элементов в списке
                    reserve_db.add_sugar(item)  # Запись данных в Резервную БД
                print("\t" + "Запись сахаров - УСПЕШНА", end="\n\n")
            else:
                print("\t" + "Записать сахаров - ОТМЕНЕНА", end="\n\n")

        # Запись данных инсулина
        if insulin:
            # Получение финальных данных
            insulin_write = new_insulin_data if edit_mode else insulin_data

            # Финальный вопрос перед записью данных
            final_test = str(input("Записать данные инсулина в Резервную БД? (YES/NO) - ")).upper()
            if final_test == "YES" or final_test == "Y":
                for item in reversed(insulin_write):  # Перебор элементов в списке
                    reserve_db.add_insulin(item)  # Запись данных в Резервную БД
                print("\t" + "Запись инсулина - УСПЕШНА", end="\n\n")
            else:
                print("\t" + "Запись инсулина - ОТМЕНЕНА", end="\n\n")

        # Запись данных устройств
        if device:
            # Получение финальных данных
            device_write = new_device_data if edit_mode else device_data

            # Финальный вопрос перед записью данных
            final_test = str(input("Записать данные устройств в Резервную БД? (YES/NO) - ")).upper()
            if final_test == "YES" or final_test == "Y":
                reserve_db.add_device(device_write)  # Запись данных в Резервную БД
                print("\t" + "Запись устройств - УСПЕШНА", end="\n\n")
            else:
                print("\t" + "Запись устройств - ОТМЕНЕНА", end="\n\n")

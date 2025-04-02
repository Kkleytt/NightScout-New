import requests  # Библиотека для отправки HTTP запросов
import datetime  # Библиотека для работы с датой и временем
from concurrent.futures import ThreadPoolExecutor  # Библиотека для работы с много поточностью
from time import sleep  # Библиотека для работы с задержкой
import json  # Библиотека для работы с JSON строками
import config as sc  # Настройки программы


# Аутентификация в API
def auth_api():
    """Функция для авторизации пользователя и получения JWT токена"""
    url = f"{sc.Parser.API.main_url}/token"
    data = {"username": sc.Parser.API.user_login, "password": sc.Parser.API.user_password}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("Ошибка авторизации:", response.text)
        return False


# Парсинг данных
def parse_data():
    """
    Функция для парсинга данных с API NightScout
    :return: JSON данные парсинга
    """

    def fetch_data(url_site):
        """Функция для получения данных с сервера
        :param url_site: Адрес NightScout API для получения данных
        """
        with requests.Session() as session:
            try:
                headers = {"accept": "application/json"}
                response = session.get(url_site, headers=headers)
                return response.json() if response.status_code == 200 else []
            except Exception as e:
                print(f"Ошибка при парсинге данных {url_site} - {e}")
                return None

    def process_sugar_data(data_sugar):
        """
        Функция обработки данных сахаров
        :param data_sugar: Необработанные JSON данные сахаров
        :return: Обработанные JSON данные сахаров
        """

        try:
            return [
                [
                    (datetime.datetime.strptime(entry['dateString'], "%Y-%m-%dT%H:%M:%S.%fZ")
                     + datetime.timedelta(hours=3)).strftime("%Y-%m-%d-%H-%M"),
                    round(int(entry['sgv']) / 18, 1),
                    entry.get('device', ''),
                    entry.get('direction', '')
                ]
                for entry in data_sugar
                if all(key in entry for key in ['dateString', 'sgv'])  # Проверка существования ключей
            ]
        except Exception as e:
            print(f"Ошибка при обработке данных сахара - {e}")
            exit(302)

    def process_insulin_data(data_insulin):
        """
        Функция обработки данных инсулина и еды
        :param data_insulin: Необработанные JSON данные инсулина и еды
        :return: Обработанные JSON данные инсулина и еды
        """

        try:
            insulin_data = []
            for entry in data_insulin:
                date = (datetime.datetime.strptime(entry['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ") +
                        datetime.timedelta(hours=3)).strftime("%Y-%m-%d-%H-%M")
                event = entry['eventType']
                duration = entry.get('duration')
                if duration:
                    duration_insulin = int(duration) if int(duration) >= 30 else 30
                else:
                    duration_insulin = 0
                match entry.get('eventType'):
                    case 'Temp Basal':
                        insulin_data.append([date, entry.get('rate'), "0", duration_insulin, event])
                    case 'Carb Correction':
                        insulin_data.append([date, "None", entry.get('carbs'), entry.get('absorptionTime'), event])
                    case 'Correction Bolus':
                        insulin_data.append([date, entry.get('insulin'), "0", "0", event])
            return insulin_data
        except Exception as e:
            print(f"Ошибка при обработке данных инсулина - {e}")
            exit(303)

    def process_device_data(data_device):
        """
        Функция обработки данных устройств
        :param data_device: Необработанные JSON данные устройств
        :return: Обработанные JSON данные устройств
        """

        try:
            search_battery_transmitter = True
            search_battery_phone = True
            search_battery_pump = True
            search_cartridge_pump = True

            device_data = {}

            for item in data_device:
                if search_battery_pump:
                    if item.get('pump', {}).get('battery', {}).get('percent') is not None:
                        device_data['battery_pump'] = item.get('pump', {}).get('battery', {}).get('percent')
                        search_battery_pump = False
                if search_cartridge_pump:
                    if item.get('pump', {}).get('reservoir') is not None:
                        device_data['cartridge_pump'] = item.get('pump', {}).get('reservoir')
                        device_data['date'] = (datetime.datetime.strptime(item['created_at'],
                                                                          "%Y-%m-%dT%H:%M:%S.%fZ") +
                                               datetime.timedelta(hours=3)).strftime("%Y-%m-%d-%H-%M")
                        device_data['model'] = (f"{item.get('pump', {}).get('manufacturer')} "
                                                f"{item.get('pump', {}).get('model')}")
                        search_cartridge_pump = False
                if 'name' in item.get('uploader', {}):
                    if item.get('uploader', {}).get('name') == 'transmitter' and search_battery_transmitter:
                        device_data['battery_transmitter'] = item.get('uploader', {}).get('battery')
                        search_battery_transmitter = False
                        continue
                    if item.get('uploader', {}).get('timestamp') is not None and search_battery_phone:
                        device_data['battery_phone'] = item.get('uploader', {}).get('battery')
                        search_battery_phone = False
                        continue
                    if item.get('uploader', {}).get('timestamp') is None and search_battery_transmitter:
                        if item.get('uploader', {}).get('name') != 'transmitter':
                            device_data['battery_transmitter'] = item.get('uploader', {}).get('battery')
                            search_battery_transmitter = False
                if 'name' not in item.get('uploader', {}) and search_battery_phone:
                    device_data['battery_phone'] = item.get('uploader', {}).get('battery')
                    search_battery_phone = False

            device_data['pump_model'] = sc.Parser.Setting.Names.pump
            device_data['phone_model'] = sc.Parser.Setting.Names.phone
            device_data['transmitter_model'] = sc.Parser.Setting.Names.transmitter

            return device_data
        except Exception as e:
            print(f"Ошибка при обработке данных сахара - {e}")
            exit(304)

    def search_data():
        """
        Функция парсинга всех данных с API NightScout
        :return: Обработанные JSON данные сахаров, инсулина и устройств
        """
        try:

            url = sc.Parser.NightScout.url
            token = sc.Parser.NightScout.token
            count = sc.Parser.NightScout.count

            if url is None or token is None or count is None:
                print("Неправильно заполнены данные для отправки запросов в NightScout")
                exit(305)

            urls = {
                "sugar": f"https://{url}/api/v1/entries/?count={count}&token={token}",
                "insulin": f"https://{url}/api/v1/treatments/?count={count}&token={token}",
                "device": f"https://{url}/api/v1/devicestatus/?count={count}&token={token}"
            }

            all_data = {}
            with ThreadPoolExecutor():
                # Выполняем запросы параллельно
                results = {key: fetch_data(url) for key, url in urls.items() if url}

                # Обрабатываем результаты запросов
                if sc.Parser.Setting.Search.sugar and results['sugar'] is not None:
                    all_data["sugar"] = process_sugar_data(results["sugar"])
                else:
                    all_data['sugar'] = results['sugar']

                if sc.Parser.Setting.Search.insulin and results['insulin'] is not None:
                    all_data["insulin"] = process_insulin_data(results["insulin"])
                else:
                    all_data['insulin'] = results['insulin']

                if sc.Parser.Setting.Search.device and results['device'] is not None:
                    all_data["device"] = process_device_data(results["device"])
                else:
                    all_data['device'] = results['device']

            return all_data
        except Exception as e:
            print(f"Ошибка при парсинге всех данных - {e}")
            exit(306)

    return search_data()


# Функция записи новых данных сахаров в БД
def write_sugar_data(data, token):
    """
    Функция для цикличной записи данных сахаров в БД (MySQL)
    :param data: Новые JSON данные сахаров
    :param token: JWT-токен для обращения к API
    :return: Результат сохранения
    """

    def generate_new_id(old_id):
        """
        Функция для генерации уникального идентификатора на основе старого
        :param old_id: Идентификатор последней записи в БД
        :return: Идентификатор для новой записи в формате xxxx:xxxx:xxxx
        """
        new_int_id = int(str(old_id).replace(":", "")) + 1
        new_str_id = f"{'0' * (12 - len(str(new_int_id)))}{str(new_int_id)}"
        new_str_id = f"{new_str_id[0:4]}:{new_str_id[4:8]}:{new_str_id[8:12]}"
        return new_str_id

    json_data = {
        'query': "SELECT id, date, sugar FROM Sugar ORDER BY date DESC LIMIT 2",
        'params': []
    }
    main_url = sc.Parser.API.main_url
    headers = {"Authorization": f"Bearer {token}"}

    # Получение старых записей в БД
    try:
        url = f"{main_url}/put/command"
        old_sugar_data = requests.put(url=url, json=json_data, headers=headers).json()
    except Exception as e:
        old_sugar_data = {}
        print(f"Ошибка получения старых данных сахаров - {e}")

    # Проверка на наличие старых записей в БД
    try:
        if len(old_sugar_data[0]) >= 3:
            bd_id = old_sugar_data[0][0]
            bd_date = old_sugar_data[0][1]
            bd_sugar = old_sugar_data[0][2]
        else:
            bd_id = 0
            bd_date = None
            bd_sugar = None
    except Exception as e:
        print(f"Ошибка получения старых данных сахаров - {e}")
        bd_id = 0
        bd_date = None
        bd_sugar = None

    # Перебор полученных с API элементов
    try:
        for item in reversed(data):
            try:

                # Проверка, что новый элемент моложе самого молодого объекта в БД
                if bd_date and bd_id and bd_sugar and item[0] > bd_date:

                    # Генерация нового id в формате xxxx:xxxx:xxxx
                    new_id = generate_new_id(bd_id)
                    bd_id = new_id

                    # Получение разницы с предыдущим сахаром
                    difference = round(item[1] - bd_sugar, 1)
                    difference = str(difference) if difference <= 0 else f"+{difference}"
                    bd_sugar = item[1]

                    # Запись новых данных в БД
                    try:
                        # Выпрямление данных
                        date = item[0]
                        sugar = float(item[1])
                        tendency = item[3]

                        # Запись данных
                        params = {
                            'id': new_id,
                            'date': date,
                            'sugar': sugar,
                            'tendency': tendency,
                            'difference': difference
                        }
                        url = f"{main_url}/put/sugar"
                        requests.put(url=url, json=params, headers=headers)

                    except Exception as e:
                        print(f"Ошибка сохранения данных сахара в БД - {e}")
                        return False

            except Exception as e:
                print(f"Ошибка при генерации данных сахаров - {e}")
                return False

        return True

    except Exception as e:
        print(f"Ошибка при переборе данных сахаров - {e}")
        return False


# Функция записи новых данных инсулина и еды в БД
def write_insulin_data(data, token):
    """
    Функция для цикличной записи данных инсулина и еды в БД (MySQL)
    :param data: Новые JSON данные сахаров
    :param token: JWT-токен для обращения к API
    :return: Результат сохранения
    """

    def generate_new_id(old_id):
        """
        Функция для генерации уникального идентификатора на основе старого
        :param old_id: Идентификатор последней записи в БД
        :return: Идентификатор для новой записи в формате xxxx:xxxx:xxxx
        """

        new_int_id = int(str(old_id).replace(":", "")) + 1
        new_str_id = f"{'0' * (12 - len(str(new_int_id)))}{str(new_int_id)}"
        new_str_id = f"{new_str_id[0:4]}:{new_str_id[4:8]}:{new_str_id[8:12]}"
        return new_str_id

    json_data = {
        'query': "SELECT * FROM Insulin ORDER BY date DESC LIMIT 1",
        'params': []
    }
    headers = {"Authorization": f"Bearer {token}"}
    main_url = sc.Parser.API.main_url

    # Получение старых записей в БД
    try:
        url = f"{main_url}/put/command"
        old_insulin_data = requests.put(url=url, json=json_data, headers=headers).json()
        old_insulin_data = list(old_insulin_data[0])
    except Exception as e:
        old_insulin_data = []
        print(f"Ошибка получения старых данных инсулина и еды - {e}")

    # Проверка на наличие старых записей в БД
    try:
        if len(old_insulin_data) >= 2:
            bd_id = old_insulin_data[0]
            bd_date = old_insulin_data[1]
        else:
            bd_id = None
            bd_date = None
    except Exception as e:
        print(f"Ошибка получения старых данных инсулина - {e}")
        bd_id = None
        bd_date = None

    # Перебор полученных с API элементов
    try:
        # Перебор полученных данных с NightScout
        for item in reversed(data):
            try:
                # Сравнение дат последнего
                if bd_id and bd_date and item[0] > bd_date:
                    # Генерация нового id в формате xxxx:xxxx:xxxx
                    new_id = generate_new_id(bd_id)
                    bd_id = new_id

                    # Генерация новых данных
                    actual_row = [
                        new_id,
                        item[0],
                        float(item[1]) if item[1] != 'None' else None,
                        float(item[2]) if item[2] != 'None' else None,
                        str(item[3]) if item[3] != 'None' else None,
                        item[4] if item[4] != 'None' else None
                    ]

                    # Проверка на схождение данных
                    if old_insulin_data[1::] == actual_row[1::]:
                        continue

                    # Попытка записи новых данных
                    try:
                        params = {
                            'id': actual_row[0],
                            'date': actual_row[1],
                            'insulin': actual_row[2],
                            'carbs': actual_row[3],
                            'duration': actual_row[4],
                            'type': actual_row[5]
                        }
                        url = f"{main_url}/put/insulin"
                        requests.put(url=url, json=params, headers=headers)
                    except Exception as e:
                        print(f"Ошибка сохранения данных инсулина и еды - {e}")
                        return False

            except Exception as e:
                print(f"Ошибка при генерации данных инсулина и еды - {e}")
                return False

        return True

    except Exception as e:
        print(f"Ошибка перебора данных инсулина и еды - {e}")
        return False


# Функция записи новых данных устройств в БД
def write_device_data(data, token):
    def comparison_data(new_data: dict, old_data: list) -> bool:
        """
        Функция для сравнения новых и старых данных
        :param new_data: Словарь новых данных
        :param old_data: Список старых данных
        :return:
        """

        # Ключи, соответствующие данным в списке
        keys = ['id', 'date', 'phone_battery', 'transmitter_battery', 'pump_battery', 'pump_cartridge',
                'cannula', 'insulin', 'sensor', 'pump_model', 'phone_model', 'transmitter_model']

        # Преобразование списка в словарь
        old_data_dict = dict(zip(keys, old_data))

        # Преобразование в JSON-строки для точного сравнения
        old_json = json.dumps(old_data_dict, sort_keys=True)
        new_json = json.dumps(new_data, sort_keys=True)

        # Сравнение
        return old_json != new_json

    """
    Функция для цикличной записи данных устройств в БД (MySQL)
    :param data: Новые JSON данные сахаров
    :param token: JWT-токен для обращения к API
    :return: Результат сохранения
    """

    try:
        # Получение последних данных устройств из БД
        json_data = {
            'query': "SELECT * FROM Device",
            'params': []
        }
        headers = {"Authorization": f"Bearer {token}"}
        main_url = sc.Parser.API.main_url

        url = f'{main_url}/put/command'
        old_device_data = requests.put(url=url, json=json_data, headers=headers).json()
        result = list(old_device_data[0])

        # Обновление данных в таблице
        if len(result) > 0:
            # Генерация запроса
            params = {
                'id': 0,
                'date': data['date'],
                'phone_battery': data['battery_phone'],
                'transmitter_battery': data['battery_transmitter'],
                'pump_battery': data['battery_pump'],
                'pump_cartridge': data['cartridge_pump'],
                'cannula': None,
                'insulin': None,
                'sensor': None,
                'pump_model': data['pump_model'],
                'phone_model': data['phone_model'],
                'transmitter_model': data['transmitter_model']
            }

            # Проверка на отличие новых данные от старых
            if comparison_data(old_data=result, new_data=params):
                url = f'{main_url}/post/device'
                requests.post(url=url, json=params, headers=headers).json()

        # Запись данных в пустую таблицу
        else:
            # Генерация запроса
            params = {
                'id': 0,
                'date': data['date'],
                'phone_battery': data['battery_phone'],
                'transmitter_battery': data['battery_transmitter'],
                'pump_battery': data['battery_pump'],
                'pump_cartridge': data['cartridge_pump'],
                'cannula': None,
                'insulin': None,
                'sensor': None,
                'pump_model': data['pump_model'],
                'phone_model': data['phone_model'],
                'transmitter_model': data['transmitter_model']
            }
            url = f'{main_url}/put/device'
            requests.put(url=url, json=params, headers=headers).json()

        return True

    except Exception as e:
        print(f"Ошибка сохранения данных устройств - {e}")
        return False


# Функция последовательной записи новых данных в БД
def start():
    # Получение всех новых данных
    all_data = parse_data()

    # Предопределение результатов парсинга
    result_sugar = None
    result_insulin = None
    result_device = None

    # Подключение к API
    api_token = auth_api()

    if not api_token:
        return False

    # Проверка на сохранение данных сахаров
    if sc.Parser.Setting.Search.sugar and all_data['sugar'] is not None:
        result_sugar = write_sugar_data(
            data=all_data['sugar'],
            token=api_token
        )

    if sc.Parser.Setting.Search.insulin and all_data['insulin'] is not None:
        result_insulin = write_insulin_data(
            data=all_data['insulin'],
            token=api_token
        )

    if sc.Parser.Setting.Search.device and all_data['device'] is not None:
        result_device = write_device_data(
            data=all_data['device'],
            token=api_token
        )

    return [
        result_sugar,
        result_insulin,
        result_device
    ]


# Функция цикличного парсинга и записи новых данных в БД
def start_loop():
    # Подключение к API, получение токена, сохранение времени получения
    api_token = auth_api()
    token_creation_time = datetime.datetime.now()

    # Проверка существования токена
    if not api_token:
        return False

    # Цикл парсинга и сохранения данных
    while True:
        # Проверка, истёк ли срок действия токена
        if datetime.datetime.now() >= token_creation_time + datetime.timedelta(minutes=sc.API.life_token):
            api_token = auth_api()
            if not api_token:
                return False
            token_creation_time = datetime.datetime.now()

        # Получение всех новых данных
        all_data = parse_data()

        # Проверка на наличие данных с NightScout
        if all_data is not None:
            if sc.Parser.Setting.Search.sugar and all_data['sugar'] is not None:
                write_sugar_data(
                    data=all_data['sugar'],
                    token=api_token
                )

            if sc.Parser.Setting.Search.insulin and all_data['insulin'] is not None:
                write_insulin_data(
                    data=all_data['insulin'],
                    token=api_token
                )

            if sc.Parser.Setting.Search.device and all_data['device'] is not None:
                write_device_data(
                    data=all_data['device'],
                    token=api_token
                )

        sleep(sc.Loop.timeout)


if __name__ == "__main__":
    start()

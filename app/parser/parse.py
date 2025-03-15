import requests
import commentjson as json
import os
import datetime
from concurrent.futures import ThreadPoolExecutor
from database.database import send_request_db


# Функция чтения конфига в нужной директории
def read_config():
    try:
        work_dir = os.getcwd()  # Текущая рабочая директория
        module = "parser"  # Имя поддиректории с модулем
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


# Парсинг данных
def parse_data(settings):
    """
    Функция для парсинга данных с API NightScout
    :param settings: JSON данные с настройками модуля
    :return: JSON данные парсинга
    """

    def fetch_data(url_site, request_headers):
        """Функция для получения данных с сервера"""
        try:
            response = requests.get(url_site, headers=request_headers)
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Ошибка при парсинге данных {url_site} - {e}")
            exit(301)

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
                    round(int(entry['sgv']) / 18, 1) if settings['sugar_to_mmol'] else entry['sgv'],
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
                        insulin_data.append([date, entry.get('rate'), "None", "None", duration_insulin, event])
                    case 'Bolus':
                        insulin_data.append([date, "None", entry.get('insulin'), "None", "0", event])
                    case 'Carb Correction':
                        insulin_data.append([date, "None", "None", entry.get('carbs'), "0", event])
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
                            print('2')
                            device_data['battery_transmitter'] = item.get('uploader', {}).get('battery')
                            search_battery_transmitter = False
                if 'name' not in item.get('uploader', {}) and search_battery_phone:
                    print('1')
                    device_data['battery_phone'] = item.get('uploader', {}).get('battery')
                    search_battery_phone = False

            device_data['pump_model'] = settings['names']['pump']
            device_data['phone_model'] = settings['names']['phone']
            device_data['transmitter_model'] = settings['names']['transmitter']

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

            url = settings['access']['url']
            token = settings['access']['token']
            count = settings['access']['count']
            headers = {"accept": "application/json"}

            if url is None or token is None or count is None:
                print("Неправильно заполнены данные для отправки запросов в NightScout")
                exit(305)

            urls = {
                "sugar": f"https://{url}/api/v1/entries/?count={count}&token={token}",
                "insulin": f"https://{url}/api/v1/treatments/?count={count}&token={token}",
                "device": f"https://{url}/api/v1/devicestatus/?count={count}&token={token}"
            }

            all_data = {}
            with ThreadPoolExecutor() as executor:
                # Выполняем запросы параллельно
                results = {key: executor.submit(fetch_data, url, headers) for key, url in urls.items() if url}

                # Обрабатываем результаты запросов
                if settings['search']['sugar']:
                    all_data["sugar"] = process_sugar_data(results["sugar"].result())

                if settings['search']['insulin']:
                    all_data["insulin"] = process_insulin_data(results["insulin"].result())

                if settings['search']['device']:
                    all_data["device"] = process_device_data(results["device"].result())

            return all_data
        except Exception as e:
            print(f"Ошибка при парсинге всех данных - {e}")
            exit(306)

    return search_data()


# Функция записи новых данных сахаров в БД
def write_sugar_data(connection, cursor, data):
    """
    Функция для цикличной записи данных сахаров в БД (MySQL)
    :param connection: Объект соединения БД
    :param cursor: Объект курсора БД
    :param data: Новые JSON данные сахаров
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

    # Получение старых записей в БД
    try:
        query = "SELECT id, date, sugar FROM Sugar ORDER BY date DESC LIMIT 2"
        old_sugar_data = send_request_db(
            connection=connection,
            cursor=cursor,
            query=query
        )
        old_sugar_data = list(old_sugar_data)
    except Exception as e:
        old_sugar_data = []
        print(f"Ошибка получения старых данных сахаров - {e}")

    # Проверка на наличие старых записей в БД
    if len(old_sugar_data[0]) >= 3:
        bd_id = old_sugar_data[0][0]
        bd_date = old_sugar_data[0][1]
        bd_sugar = old_sugar_data[0][2]
    else:
        bd_id = None
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
                        query = "INSERT INTO Sugar VALUES (%s, %s, %s, %s, %s)"
                        new_data = [
                            new_id,
                            date,
                            sugar,
                            tendency,
                            difference
                        ]
                        send_request_db(
                            connection=connection,
                            cursor=cursor,
                            query=query,
                            data=new_data
                        )

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
def write_insulin_data(connection, cursor, data):
    """
    Функция для цикличной записи данных инсулина и еды в БД (MySQL)
    :param connection: Объект соединения БД
    :param cursor: Объект курсора БД
    :param data: Новые JSON данные сахаров
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

    # Получение старых записей в БД
    try:
        query = "SELECT id, date FROM Insulin ORDER BY date DESC LIMIT 1"
        old_insulin_data = send_request_db(
            connection=connection,
            cursor=cursor,
            query=query
        )
        old_insulin_data = list(old_insulin_data[0])
    except Exception as e:
        old_insulin_data = []
        print(f"Ошибка получения старых данных инсулина и еды - {e}")

    # Проверка на наличие старых записей в БД
    if len(old_insulin_data) >= 2:
        bd_id = old_insulin_data[0]
        bd_date = old_insulin_data[1]
    else:
        bd_id = None
        bd_date = None

    # Перебор полученных с API элементов
    try:
        for item in reversed(data):
            try:
                # Сравнение дат последнего
                if bd_id and bd_date and item[0] > bd_date:

                    # Генерация нового id в формате xxxx:xxxx:xxxx
                    new_id = generate_new_id(bd_id)
                    bd_id = new_id

                    # Проверка прошлой записи в БД
                    query = "SELECT * FROM Insulin ORDER BY date DESC LIMIT 1"
                    preview_row = send_request_db(
                        connection=connection,
                        cursor=cursor,
                        query=query
                    )
                    preview_row = list(preview_row[0])

                    # Генерация новых данных
                    actual_row = [
                        new_id,
                        item[0],
                        item[1] if item[1] != 'None' else None,
                        item[2] if item[2] != 'None' else None,
                        item[3] if item[3] != 'None' else None,
                        item[4] if item[4] != 'None' else None,
                        item[5] if item[5] != 'None' else None
                    ]

                    # Проверка на схождение данных
                    if preview_row[1::] == actual_row[1::]:
                        continue

                    # Попытка записи новых данных
                    try:
                        query = "INSERT INTO Insulin VALUES (%s, %s, %s, %s, %s, %s, %s)"
                        send_request_db(
                            connection=connection,
                            cursor=cursor,
                            query=query,
                            data=actual_row
                        )
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
def write_device_data(connection, cursor, data):
    """
    Функция для цикличной записи данных устройств в БД (MySQL)
    :param connection: Объект соединения БД
    :param cursor: Объект курсора БД
    :param data: Новые JSON данные сахаров
    :return: Результат сохранения
    """

    try:
        # Получение последних данных устройств из БД
        query = "SELECT id FROM Device"
        old_device_data = send_request_db(
            connection=connection,
            cursor=cursor,
            query=query
        )
        result = list(old_device_data[0])

        # Обновление данных в таблице
        if len(result) > 0:
            # Генерация запроса
            query = f"""
                UPDATE Device SET 
                date = %s,
                phone_battery = %s, 
                transmitter_battery = %s,
                pump_battery = %s,
                pump_cartridge = %s, 
                pump_model = %s,
                phone_model = %s,
                transmitter_model = %s
                WHERE id = 0;
            """
            new_data = [
                data['date'],
                data['battery_phone'],
                data['battery_transmitter'],
                data['battery_pump'],
                data['cartridge_pump'],
                data['pump_model'],
                data['phone_model'],
                data['transmitter_model']
            ]

            # Обновление данных в таблице
            send_request_db(
                connection=connection,
                cursor=cursor,
                query=query,
                data=new_data
            )

        # Запись данных в пустую таблицу
        else:
            # Генерация запроса
            query = """INSERT INTO Device (
            id, 
            date, 
            phone_battery, 
            transmitter_battery, 
            pump_battery, 
            pump_cartridge, 
            pump_model, 
            phone_model, 
            transmitter_model
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            new_data = [
                0,
                data['date'],
                data['battery_phone'],
                data['battery_transmitter'],
                data['battery_pump'],
                data['cartridge_pump'],
                data['pump_model'],
                data['phone_model'],
                data['transmitter_model']
            ]

            # Обновление данных в таблице
            send_request_db(
                connection=connection,
                cursor=cursor,
                query=query,
                data=new_data
            )

        return True

    except Exception as e:
        print(f"Ошибка сохранения данных устройств - {e}")
        return False


# Функция последовательной записи новых данных в БД
def write_data(connection, cursor, settings):

    # Получение всех новых данных
    all_data = parse_data(settings=settings)

    # Предопределение результатов парсинга
    result_sugar = None
    result_insulin = None
    result_device = None

    # Проверка на сохранение данных сахаров
    if settings['search']['sugar']:
        result_sugar = write_sugar_data(
            connection=connection,
            cursor=cursor,
            data=all_data['sugar'],
        )

    if settings['search']['insulin']:
        result_insulin = write_insulin_data(
            cursor=cursor,
            connection=connection,
            data=all_data['insulin'],
        )

    if settings['search']['device']:
        result_device = write_device_data(
            cursor=cursor,
            connection=connection,
            data=all_data['device'],
        )

    return [
        result_sugar,
        result_insulin,
        result_device
    ]


# Функция одного парсинга и записи данных
def start(connection, cursor):
    """
    Функция парсинга и сохранения данных
    :param connection: Объект соединения БД (MySQL)
    :param cursor: Объект курсора БД (MySQL)
    :return: None
    """

    # Чтение настроек модуля
    settings = read_config()

    results = write_data(
        connection=connection,
        cursor=cursor,
        settings=settings
    )

    return results

from fastapi import FastAPI, HTTPException  # Библиотека для работы с FastAPI
import uvicorn  # Библиотека для работы с локальным сервером
from database import database as db  # Модуль для взаимодействия с БД
from database import struct  # Модуль с описанием структуры таблицы в БД
import os  # Библиотека для работы с файловой системой
import commentjson as json  # Библиотека для работы с JSON строками


# Функция чтения конфига в нужной директории
def read_config():
    """
    Функция чтения настроек модуля
    :return: JSON объект
    """

    try:
        work_dir = os.getcwd()  # Текущая рабочая директория
        module = "api"  # Имя поддиректории с модулем
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


# Функция для генерации уникального идентификатора на основе числа
def generate_new_id(old_id):
    """
    Функция для генерации уникального идентификатора на основе числа
    :param old_id: Идентификатор последней записи в БД
    :return: Идентификатор для новой записи в формате xxxx:xxxx:xxxx
    """

    new_int_id = int(str(old_id).replace(":", ""))
    new_str_id = f"{'0' * (12 - len(str(new_int_id)))}{str(new_int_id)}"
    new_str_id = f"{new_str_id[0:4]}:{new_str_id[4:8]}:{new_str_id[8:12]}"
    return new_str_id


# Функция создания FastAPI-приложения
def create_app(connection, cursor, settings):
    """
    Функция запуска FastAPI-приложения
    :param connection: Объект соединения БД (MySQL)
    :param cursor: Объект курсора БД (MySQL)
    :param settings: Объект настроек модуля
    :return: None
    """

    # Создание API приложения
    app = FastAPI(title="Sugar Tracking API", version="1.0.0")

    # Функция отправки запросов и получении данных в БД
    @app.put("/put/command/token={token}")
    async def get_data_by_command(token: str, data: struct.CommandData):
        # Проверка на доступ к данному виду запросов
        if not settings['rules']['get']:
            raise HTTPException(status_code=400, detail="Method POST is not Allowed")

        # Проверка на верный токен доступа
        if token != settings['token']:
            raise HTTPException(status_code=400, detail="Token is not Valid")

        # Генерация запроса и получение данных
        try:
            result = db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=data.query,
                data=data.params
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data is not valid. Error - {e}")

    # Функция получение записи в таблице Sugar по ID
    @app.get("/get/sugar/id/token={token}&id={record_id}")
    async def get_glucose_by_id(token: str, record_id: int):
        # Проверка на доступ к данному виду запросов
        if not settings['rules']['get']:
            raise HTTPException(status_code=400, detail="Method POST is not Allowed")

        # Проверка на верный токен доступа
        if token != settings['token']:
            raise HTTPException(status_code=400, detail="Token is not Valid")

        # Генерация запроса и передача данных
        try:
            sugar_id = str(generate_new_id(record_id))

            query = "SELECT * FROM Sugar WHERE id = %s"
            result = db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query,
                data=sugar_id
            )

            return {
                "id": result[0][0],
                "date": result[0][1],
                "sugar": result[0][2],
                "tendency": result[0][3],
                "difference": result[0][4]
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data is not valid. Error - {e}")

    # Функция получение записей в таблице Sugar по разрезу дат
    @app.get("/get/sugar/date/token={token}&start={date_start}&end={date_end}")
    async def get_sugar_by_date(token: str, date_start: str, date_end: str):
        # Проверка на доступ к данному виду запросов
        if not settings['rules']['get']:
            raise HTTPException(status_code=400, detail="Method POST is not Allowed")

        # Проверка на верный токен доступа
        if token != settings['token']:
            raise HTTPException(status_code=400, detail="Token is not Valid")

        # Генерация запроса и передача данных
        try:
            query = "SELECT * FROM Sugar WHERE date BETWEEN %s AND %s"
            result = db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query,
                data=[date_start, date_end]
            )
            json_results = {}

            for item in result:
                json_results[item[0]] = {
                    "id": item[0],
                    "date": item[1],
                    "sugar": item[2],
                    "tendency": item[3],
                    "difference": item[4]
                }

            return json_results
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data is not valid. Error - {e}")

    # Функция получение записи в таблице Insulin по ID
    @app.get("/get/insulin/id/token={token}&id={record_id}")
    async def get_insulin_by_id(token: str, record_id: int):
        # Проверка на доступ к данному виду запросов
        if not settings['rules']['get']:
            raise HTTPException(status_code=400, detail="Method POST is not Allowed")

        # Проверка на верный токен доступа
        if token != settings['token']:
            raise HTTPException(status_code=400, detail="Token is not Valid")

        # Генерация запроса и передача данных
        try:
            insulin_id = str(generate_new_id(record_id))

            query = "SELECT * FROM Insulin WHERE id = %s"
            result = db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query,
                data=insulin_id
            )

            return {
                "id": result[0][0],
                "date": result[0][1],
                "insulin": result[0][2],
                "carbs": result[0][3],
                "duration": result[0][4],
                "type": result[0][5],
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data is not valid. Error - {e}")

    # Функция получение записей в таблице Insulin по разрезу дат
    @app.get("/get/insulin/date/token={token}&start={date_start}&end={date_end}")
    async def get_insulin_by_date(token: str, date_start: str, date_end: str):
        # Проверка на доступ к данному виду запросов
        if not settings['rules']['get']:
            raise HTTPException(status_code=400, detail="Method POST is not Allowed")

        # Проверка на верный токен доступа
        if token != settings['token']:
            raise HTTPException(status_code=400, detail="Token is not Valid")

        # Генерация запроса и передача данных
        try:
            query = "SELECT * FROM Insulin WHERE date BETWEEN %s AND %s"
            result = db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query,
                data=[date_start, date_end]
            )
            json_results = {}

            for item in result:
                json_results[item[0]] = {
                    "id": item[0],
                    "date": item[1],
                    "insulin": item[2],
                    "carbs": item[3],
                    "duration": item[4],
                    "type": item[5]
                }

            return json_results
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data is not valid. Error - {e}")

    # Функция получение последней записи в таблице Sugar
    @app.get("/get/sugar/last/token={token}")
    async def get_sugar_by_last(token: str):
        # Проверка на доступ к данному виду запросов
        if not settings['rules']['get']:
            raise HTTPException(status_code=400, detail="Method POST is not Allowed")

        # Проверка на верный токен доступа
        if token != settings['token']:
            raise HTTPException(status_code=400, detail="Token is not Valid")

        # Генерация запроса и передача данных
        try:
            query = "SELECT * FROM Sugar ORDER BY date DESC LIMIT 1"
            result = db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query
            )
            return {
                "id": result[0][0],
                "date": result[0][1],
                "sugar": result[0][2],
                "tendency": result[0][3],
                "difference": result[0][4]
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data is not valid. Error - {e}")

    # Функция получение последней записи в таблице Insulin
    @app.get("/get/insulin/last/token={token}")
    async def get_insulin_by_last(token: str):
        # Проверка на доступ к данному виду запросов
        if not settings['rules']['get']:
            raise HTTPException(status_code=400, detail="Method POST is not Allowed")

        # Проверка на верный токен доступа
        if token != settings['token']:
            raise HTTPException(status_code=400, detail="Token is not Valid")

        # Генерация запроса и передача данных
        try:
            query = "SELECT * FROM Insulin ORDER BY date DESC LIMIT 1"
            result = db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query
            )
            return {
                "id": result[0][0],
                "date": result[0][1],
                "insulin": result[0][2],
                "carbs": result[0][3],
                "duration": result[0][4],
                "type": result[0][5],
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data is not valid. Error - {e}")

    # Функция получение последней записи в таблице Device
    @app.get("/get/device/last/token={token}")
    async def get_device_by_last(token: str):
        # Проверка на доступ к данному виду запросов
        if not settings['rules']['get']:
            raise HTTPException(status_code=400, detail="Method POST is not Allowed")

        # Проверка на верный токен доступа
        if token != settings['token']:
            raise HTTPException(status_code=400, detail="Token is not Valid")

        # Генерация запроса и передача данных
        try:
            query = "SELECT * FROM Device ORDER BY date DESC LIMIT 1"
            result = db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query
            )
            return {
                "id": result[0][0],
                "date": result[0][1],
                "phone_battery": result[0][2],
                "transmitter_battery": result[0][3],
                "pump_battery": result[0][4],
                "pump_cartridge": result[0][5],
                "cannula": result[0][6],
                "insulin": result[0][7],
                "sensor": result[0][8],
                "pump_model": result[0][9],
                "phone_model": result[0][10],
                "transmitter_model": result[0][11],
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data is not valid. Error - {e}")

    # Функция добавления данных сахара в БД
    @app.put("/put/sugar/token={token}")
    def add_sugar(token: str, data: struct.SugarData):
        # Проверка на доступ к данному виду запросов
        if not settings['rules']['put']:
            raise HTTPException(status_code=400, detail="Method POST is not Allowed")

        # Проверка на верный токен доступа
        if token != settings['token']:
            raise HTTPException(status_code=400, detail="Token is not Valid")

        # Генерация запроса и добавление данных
        try:
            query = "INSERT INTO Sugar VALUES (%s, %s, %s, %s, %s)"
            db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query,
                data=[
                    data.id,
                    data.date,
                    data.sugar,
                    data.tendency,
                    data.difference
                ]
            )
            return {"result": True}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data is not valid. Error - {e}")

    # Функция добавления данных инсулина в БД
    @app.put("/put/insulin/token={token}")
    def add_insulin(token: str, data: struct.InsulinData):
        # Проверка на доступ к данному виду запросов
        if not settings['rules']['put']:
            raise HTTPException(status_code=400, detail="Method POST is not Allowed")

        # Проверка на верный токен доступа
        if token != settings['token']:
            raise HTTPException(status_code=400, detail="Token is not Valid")

        # Генерация запроса и добавление данных
        try:
            query = "INSERT INTO Insulin VALUES (%s, %s, %s, %s, %s, %s)"
            db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query,
                data=[
                    data.id,
                    data.date,
                    data.insulin,
                    data.carbs,
                    data.duration,
                    data.type
                ]
            )
            return {"result": True}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data is not valid. Error - {e}")

    # Функция добавления данных устройств в БД
    @app.put("/put/device/token={token}")
    def add_device(token: str, data: struct.DeviceData):
        # Проверка на доступ к данному виду запросов
        if not settings['rules']['put']:
            raise HTTPException(status_code=400, detail="Method POST is not Allowed")

        # Проверка на верный токен доступа
        if token != settings['token']:
            raise HTTPException(status_code=400, detail="Token is not Valid")

        # Генерация запроса и добавление данных
        try:
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
            db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query,
                data=[
                    data.id,
                    data.date,
                    data.phone_battery,
                    data.transmitter_battery,
                    data.pump_battery,
                    data.pump_cartridge,
                    data.pump_model,
                    data.phone_model,
                    data.transmitter_model
                ]
            )
            return {"result": True}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data is not valid. Error - {e}")

    # Функция обновления данных устройств в БД
    @app.post("/post/device/token={token}")
    def update_device(token: str, data: struct.DeviceData):
        # Проверка на доступ к данному виду запросов
        if not settings['rules']['post']:
            raise HTTPException(status_code=400, detail="Method POST is not Allowed")

        # Проверка на верный токен доступа
        if token != settings['token']:
            raise HTTPException(status_code=400, detail="Token is not Valid")

        # Генерация запроса и добавление данных
        try:
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
            db.send_request_db(
                connection=connection,
                cursor=cursor,
                query=query,
                data=[
                    data.date,
                    data.phone_battery,
                    data.transmitter_battery,
                    data.pump_battery,
                    data.pump_cartridge,
                    data.pump_model,
                    data.phone_model,
                    data.transmitter_model
                ]
            )
            return {"result": True}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data is not valid. Error - {e}")

    return app


# Функция запуска API-сервера
def start(connection, cursor):
    """
    Функция запуска API-сервера
    :param connection: Объект соединения БД (MySQL)
    :param cursor: Объект курсора БД (MySQL)
    :return: None
    """

    # Чтение настроек модуля
    settings = read_config()

    # Создание внешнего объекта FastAPI приложения
    app = create_app(
        connection=connection,
        cursor=cursor,
        settings=settings
    )

    # Запуск API приложения на локальном сервера
    uvicorn.run(app, host=settings['host'], port=settings['port'])

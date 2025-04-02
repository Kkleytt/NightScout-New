from fastapi import FastAPI, HTTPException  # Библиотека для работы с FastAPI
from fastapi import Security  # Библиотека для улучшения безопасности сервера
from fastapi.security import OAuth2PasswordBearer  # Библиотека для поддержки JWT-токенов
from jose import JWTError, jwt  # Библиотека для работы с JWT ключами
from datetime import datetime, timedelta, UTC  # Библиотека для отслеживания времени
from passlib.context import CryptContext  # Библиотека для поддержки hash-шифрования
import uvicorn  # Библиотека для работы с локальным сервером
from typing import Optional  # Библиотека для поддержки опциональных типов данных
import json as js  # Библиотека для работы с JSON строками
import os  # Библиотека для работы с операционной системой

from database import database  # Модуль для взаимодействия с БД
from database import struct  # Модуль с описанием структуры таблицы в БД
import config as sc  # Настройки программы


# Класс для управления безопасностью
class JwtManager:
    def __init__(self, secret_key, algorithm, token_life, users_file_path):
        """
        Функция инициализация менеджера безопасности запросов
        :param secret_key: Секретный ключ шифрования (STR)
        :param algorithm: Алгоритм шифрования ключей (STR)
        :param token_life: Время жизни ключа (INT)
        :param users_file_path: Абсолютный путь до файла со списком пользователей (STR)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_life = token_life
        self.path_users = users_file_path
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.access_users = self.read_users()

    def read_users(self):
        """
        Функция чтения списка пользователей
        :return: JSON-строку с массивом пользователей (логинов и паролей)
        """

        with open(self.path_users, "r", encoding="utf-8") as f:
            return js.load(f)

    def save_users(self):
        with open(self.path_users, "w", encoding="utf-8") as f:
            js.dump(self.access_users, f, ensure_ascii=False, indent=4)

    def add_user(self, login, password):
        try:
            # Проверка свободного логина
            if login in self.access_users:
                print(f"User with login '{login}' already exists.")
                return False

            # Добавление пользователя в КЭШ
            self.access_users[login] = {
                "username": login,
                "password": password
            }

            # Сохранение пользователей в Файл
            self.save_users()
            print(f"User '{login}' added successfully.")
            return True
        except Exception:
            return False

    def verify_password(self, plain_password: str, password: str) -> bool:
        """
        Функция верификации хэш паролей (сравнение)
        :param plain_password: Пароль пользователя из БД
        :param password: Пароль переданный пользователем
        :return: Результат сравнения (True | False)
        """
        return self.pwd_context.verify(plain_password, password)

    def get_password_hash(self, password: str) -> str:
        """
        Функция для перевода пароля в хэш
        :param password: Пароль для преобразования
        :return: Пароль в виде хэша
        """

        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Функция создания токена
        :param data: JSON строка с именем пользователя
        :param expires_delta: Время жизни токена
        :return: JWT-токен
        """

        to_encode = data.copy()
        expire = datetime.now(UTC) + (expires_delta if expires_delta else timedelta(minutes=self.token_life))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        return encoded_jwt

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """
        Функция авторизации пользователя (Проверка логина + пароля)
        :param username: Логин пользователя
        :param password: Пароль пользователя
        :return: Результат проверки
        """

        user = self.access_users.get(username)
        if not user or not self.verify_password(password, self.pwd_context.hash(user["password"])):
            return None
        return user

    def get_current_user(self, token: str) -> dict:
        """
        Проверка подлинности JWT-токена
        :param token: JWT-токен переданный пользователем
        :return: Результат верификации
        """

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return {"Result": False, "Detail": "Invalid token", "Code": 401}
            return {"Result": True, "Detail": username, "Code": 200}
        except JWTError:
            return {"Result": False, "Detail": "Could not validate credentials", "Code": 401}


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


# Функция для верификации запросов
def verification_client(token, secret_key, algorithm, method="GET"):
    """
    Функция для верификации запросов
    :param token: JWT-токен переданный клиентом
    :param secret_key: Секретный ключ шифрования токенов
    :param algorithm: Алгоритм шифрования данных
    :param method: Метод запроса
    :return: JSON-ответ с результатом верификации
    """

    # Проверка на включенный метод
    if not eval(f"sc.API.Methods.{method.lower()}"):
        return {"Result": False, "Detail": f"Method {method} Not Allowed", "Code": 401}

    # Проверка JWT-токена
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        username: str = payload.get("sub")
        if username is None:
            return {"Result": False, "Detail": f"Token is not Valid", "Code": 401}
    except JWTError:
        return {"Result": False, "Detail": "Could not validate credentials", "Code": 401}

    return {"Result": True, "Detail": f"Grant access - OK", "Code": 200}


# Функция создания FastAPI-приложения
def create_app():
    # Создание API приложения
    app = FastAPI(title="Sugar Tracking API", version="1.0.0")

    # Подключение к БД (MySQL)
    db = database.MySQL(
        host=sc.DataBase.host,
        port=sc.DataBase.port,
        user=eval(f"sc.DataBase.{sc.DataBase.sel_user}.login"),
        password=eval(f"sc.DataBase.{sc.DataBase.sel_user}.password"),
        database=sc.DataBase.database,
        retry_max=sc.DataBase.retry_max,
        retry_delay=sc.DataBase.retry_delay,
        timeout=sc.DataBase.timeout,
        read_timeout=sc.DataBase.read_timeout,
        write_timeout=sc.DataBase.write_timeout
    )

    # Инициализация менеджера аутентификации
    auth = JwtManager(
        secret_key=sc.API.token,
        algorithm="HS256",
        token_life=sc.API.life_token,
        users_file_path=os.path.abspath(os.path.join(os.getcwd(), "users.json"))
    )

    # Функция получение токена на основе логина и пароля
    @app.post("/token", response_model=struct.Token)
    def login_for_access_token(user: struct.User):
        auth_user = auth.authenticate_user(user.username, user.password)
        if not auth_user:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        access_token = auth.create_access_token(data={"sub": user.username})
        print(f"Выдан новый JWT-токен для пользователя {user.username}")
        return {"access_token": access_token, "token_type": "bearer"}

    # Функция
    @app.get("/get/secure-status")
    def get_secure_data(token: str = Security(auth.oauth2_scheme)):
        try:
            # Верификация запроса
            response = verification_client(
                token=token,
                secret_key=auth.secret_key,
                algorithm=auth.algorithm,
                method="GET"
            )
            if not response['Result']:
                raise HTTPException(
                    status_code=response['Code'],
                    detail=response['Detail']
                )
            return response
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))

    # Функция отправки запросов и получении данных в БД
    @app.put("/put/command")
    async def get_data_by_command(data: struct.CommandData, token: str = Security(auth.oauth2_scheme)):
        # Верификация запроса
        response = verification_client(
            token=token,
            secret_key=auth.secret_key,
            algorithm=auth.algorithm,
            method="PUT"
        )
        if not response['Result']:
            raise HTTPException(
                status_code=response['Code'],
                detail=response['Detail']
            )

        # Генерация запроса и получение данных
        try:
            result = db.execute_query(
                query=data.query,
                params=data.params
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data is not valid. Error - {e}")

    # Функция добавления нового пользователя в БД
    @app.put("/create/new-user")
    async def create_new_user(data: struct.User, token: str = Security(auth.oauth2_scheme)):
        # Верификация запроса
        response = verification_client(
            token=token,
            secret_key=auth.secret_key,
            algorithm=auth.algorithm,
            method="PUT"
        )
        if not response['Result']:
            raise HTTPException(
                status_code=response['Code'],
                detail=response['Detail']
            )

        # Добавление нового пользователя, запись пользователей в файл + отправка результата
        return auth.add_user(
            login=data.username,
            password=data.password
        )

    # Функция получение записи в таблице Sugar по ID
    @app.get("/get/sugar/id/id={record_id}")
    async def get_glucose_by_id(record_id: int, token: str = Security(auth.oauth2_scheme)):
        # Верификация запроса
        response = verification_client(
            token=token,
            secret_key=auth.secret_key,
            algorithm=auth.algorithm,
            method="GET"
        )
        if not response['Result']:
            raise HTTPException(
                status_code=response['Code'],
                detail=response['Error']
            )

        # Генерация запроса и передача данных
        try:
            result = db.execute_query(
                query="SELECT * FROM Sugar WHERE id = %s",
                params=str(generate_new_id(record_id))
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
    @app.get("/get/sugar/date/start={date_start}&end={date_end}")
    async def get_sugar_by_date(date_start: str, date_end: str, token: str = Security(auth.oauth2_scheme)):
        # Верификация запроса
        response = verification_client(
            token=token,
            secret_key=auth.secret_key,
            algorithm=auth.algorithm,
            method="GET"
        )
        if not response['Result']:
            raise HTTPException(
                status_code=response['Code'],
                detail=response['Error']
            )

        # Генерация запроса и передача данных
        try:
            result = db.execute_query(
                query="SELECT * FROM Sugar WHERE date BETWEEN %s AND %s",
                params=[date_start, date_end]
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
    @app.get("/get/insulin/id/id={record_id}")
    async def get_insulin_by_id(record_id: int, token: str = Security(auth.oauth2_scheme)):
        # Верификация запроса
        response = verification_client(
            token=token,
            secret_key=auth.secret_key,
            algorithm=auth.algorithm,
            method="GET"
        )
        if not response['Result']:
            raise HTTPException(
                status_code=response['Code'],
                detail=response['Error']
            )

        # Генерация запроса и передача данных
        try:
            result = db.execute_query(
                query="SELECT * FROM Insulin WHERE id = %s",
                params=str(generate_new_id(record_id))
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
    @app.get("/get/insulin/date/start={date_start}&end={date_end}")
    async def get_insulin_by_date(date_start: str, date_end: str, token: str = Security(auth.oauth2_scheme)):
        # Верификация запроса
        response = verification_client(
            token=token,
            secret_key=auth.secret_key,
            algorithm=auth.algorithm,
            method="GET"
        )
        if not response['Result']:
            raise HTTPException(
                status_code=response['Code'],
                detail=response['Error']
            )

        # Генерация запроса и передача данных
        try:
            result = db.execute_query(
                query="SELECT * FROM Insulin WHERE date BETWEEN %s AND %s",
                params=[date_start, date_end]
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
    @app.get("/get/sugar/last")
    async def get_sugar_by_last(token: str = Security(auth.oauth2_scheme)):
        # Верификация запроса
        response = verification_client(
            token=token,
            secret_key=auth.secret_key,
            algorithm=auth.algorithm,
            method="GET"
        )
        if not response['Result']:
            raise HTTPException(
                status_code=response['Code'],
                detail=response['Error']
            )

        # Генерация запроса и передача данных
        try:
            result = db.execute_query(
                query="SELECT * FROM Sugar ORDER BY date DESC LIMIT 1"
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
    @app.get("/get/insulin/last")
    async def get_insulin_by_last(token: str = Security(auth.oauth2_scheme)):
        # Верификация запроса
        response = verification_client(
            token=token,
            secret_key=auth.secret_key,
            algorithm=auth.algorithm,
            method="GET"
        )
        if not response['Result']:
            raise HTTPException(
                status_code=response['Code'],
                detail=response['Error']
            )

        # Генерация запроса и передача данных
        try:
            result = db.execute_query(
                query="SELECT * FROM Insulin ORDER BY date DESC LIMIT 1"
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
    @app.get("/get/device/last")
    async def get_device_by_last(token: str = Security(auth.oauth2_scheme)):
        # Верификация запроса
        response = verification_client(
            token=token,
            secret_key=auth.secret_key,
            algorithm=auth.algorithm,
            method="GET"
        )
        if not response['Result']:
            raise HTTPException(
                status_code=response['Code'],
                detail=response['Error']
            )

        # Генерация запроса и передача данных
        try:
            result = db.execute_query(
                query="SELECT * FROM Device ORDER BY date DESC LIMIT 1"
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
    @app.put("/put/sugar")
    def add_sugar(data: struct.SugarData, token: str = Security(auth.oauth2_scheme)):
        # Верификация запроса
        response = verification_client(
            token=token,
            secret_key=auth.secret_key,
            algorithm=auth.algorithm,
            method="PUT"
        )
        if not response['Result']:
            raise HTTPException(
                status_code=response['Code'],
                detail=response['Error']
            )

        # Генерация запроса и добавление данных
        try:
            db.execute_query(
                query="INSERT INTO Sugar VALUES (%s, %s, %s, %s, %s)",
                params=[
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
    @app.put("/put/insulin")
    def add_insulin(data: struct.InsulinData, token: str = Security(auth.oauth2_scheme)):
        # Верификация запроса
        response = verification_client(
            token=token,
            secret_key=auth.secret_key,
            algorithm=auth.algorithm,
            method="PUT"
        )
        if not response['Result']:
            raise HTTPException(
                status_code=response['Code'],
                detail=response['Error']
            )

        # Генерация запроса и добавление данных
        try:
            db.execute_query(
                query="INSERT INTO Insulin VALUES (%s, %s, %s, %s, %s, %s)",
                params=[
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
    @app.put("/put/device")
    def add_device(data: struct.DeviceData, token: str = Security(auth.oauth2_scheme)):
        # Верификация запроса
        response = verification_client(
            token=token,
            secret_key=auth.secret_key,
            algorithm=auth.algorithm,
            method="PUT"
        )
        if not response['Result']:
            raise HTTPException(
                status_code=response['Code'],
                detail=response['Error']
            )

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
            db.execute_query(
                query=query,
                params=[
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
    @app.post("/post/device")
    def update_device(data: struct.DeviceData, token: str = Security(auth.oauth2_scheme)):
        # Верификация запроса
        response = verification_client(
            token=token,
            secret_key=auth.secret_key,
            algorithm=auth.algorithm,
            method="POST"
        )
        if not response['Result']:
            raise HTTPException(
                status_code=response['Code'],
                detail=response['Error']
            )

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
            db.execute_query(
                query=query,
                params=[
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
def start():
    """
    Функция запуска API-сервера
    :return: None
    """

    # Создание внешнего объекта FastAPI приложения
    app = create_app()

    # Запуск API приложения на локальном сервера
    uvicorn.run(app, host=sc.API.host, port=sc.API.port)


if __name__ == '__main__':
    start()

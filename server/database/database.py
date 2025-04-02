import pymysql  # Библиотека для работы с БД (MySQL)
import time  # Библиотека для работы со временем


class MySQL:
    def __init__(self, host, port, user, password, database, retry_max, retry_delay, timeout, read_timeout, write_timeout):
        """
        Класс Базы Данных MySQL
        :param host: Ip-адрес для подключения к MySQL
        :param port: Порт для подключения к MySQL
        :param user: Логин пользователя для авторизации
        :param password: Пароль пользователя для авторизации
        :param database: Имя Базы Данных
        :param retry_max: Максимальное кол-во попыток подключения
        :param retry_delay: Ожидания между попытками подключения
        """

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.max_retries = retry_max
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout
        self.connection = None
        self.connect()

    def connect(self):
        """Устанавливает подключение к базе данных с обработкой ошибок"""
        retries = 0
        while retries < self.max_retries:
            try:
                self.connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    autocommit=True,  # Автоматически фиксирует изменения
                    connect_timeout=self.timeout,
                    read_timeout=self.read_timeout,
                    write_timeout=self.write_timeout
                )
                print("✅ Подключение к БД установлено")
                return
            except pymysql.err.OperationalError as e:
                print(f"⚠️ Ошибка подключения к БД: {e}, повтор через {self.retry_delay} сек...")
                time.sleep(self.retry_delay)
                retries += 1
        raise Exception("❌ Не удалось подключиться к БД после нескольких попыток")

    def reconnect_if_needed(self):
        """Проверяет, активно ли соединение, и подключается при необходимости"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except (pymysql.err.OperationalError, pymysql.err.InterfaceError):
            print("🔄 Соединение с БД потеряно, переподключение...")
            self.connect()

    def execute_query(self, query, params=None):
        """Выполняет SQL-запрос с автоматическим подключением при обрыве связи
        :param query: SQL запрос
        :param params: Параметры для запроса
        :return : Данные от БД
        """
        self.reconnect_if_needed()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except pymysql.err.OperationalError:
            print("⚠️ Ошибка запроса, попытка переподключения...")
            self.connect()
            return self.execute_query(query, params)  # Повторный запрос после переподключения

#  Параметры подключения к БД
DATABASE = {
    "Path": "database.db",  # Относительный путь до БД
    "Sugar": "Sugar",  # Название таблицы с сахарами 
    "Insulin": "Insulin",  # Название таблицы с данными о подаче инсулина
    "Device": "Device",  # Название таблицы с данными о устройствах
}

#  Параметры отображения сахара
DICT_TENDENCY = {"Flat": "➡️",  # Иконка при ровном сахара
                 "FortyFiveUp": "↗️",  # Иконка при растушем сахаре
                 "SingleUp": "⬆️",  # Иконка при быстро растущем сахаре
                 "DoubleUp": "⬆️⬆️",  # Иконка при очень быстро растущем сахаре
                 "FortyFiveDown": "↘️",  # Иконка при падающем сахаре
                 "SingleDown": "⬇️",  # Иконка при быстро падающем сахаре
                 "DoubleDown": "⬇️⬇️",  # Иконка при очень быстро растущем сахаре
                 "NOT COMPUTABLE": "❔",  # Иконка при неявных изменениях в сахаре
                 "": "❔"  # Иконка при неполных данных о сахаре с сайта NighScout
                 }
SUGAR_LEVELS = {
    (0, 3.9): "🔴",  # Критически низкий уровень сахара
    (4.0, 4.9): "🟡",  # Низкий уровень сахара
    (5.0, 7.4): "🟢",  # Нормальный уровень сахара
    (7.4, 10.0): "🟡",  # Повышенный уровень сахара
    (10.1, 40.0): "🔴"  # Критически повышенный уровень сахара
}
SUGAR_MMOL = True  # Перевод показателей сахара в Ммоль/литр (True-да/False-нет)

#  Параметры парсинга данных
SEARCH_SETTINGS = {
    "Sugar": True,  # Получать показания сахара (True-да/False-нет)
    "Insulin": True,  # Получать показания о подаче инсулина (True-да/False-нет)
    "Device": True,  # Получать показания о устройствах в системе (True-да/False-нет)
    "Count": 100  # Количество данных при запроса (чем больше - тем медленней работает, повышать при ситуациях когда программа не работла анескольок дней)
}
TOKEN = "TOKEN"  # Токен авторизации на вашем сайте NighScout
BASE_URL = "URL"  # URL адрес вашего NightScout в таком формате
URL_SUGAR = f"https://{BASE_URL}/api/v1/entries/?count={SEARCH_SETTINGS['Count']}&token={TOKEN}"  # НЕ ТРОГАТЬ
URL_INSULIN = f"https://{BASE_URL}/api/v1/treatments/?count={SEARCH_SETTINGS['Count']}&token={TOKEN}"  # НЕ ТРОГАТЬ
URL_DEVICE = f"https://{BASE_URL}/api/v1/devicestatus/?count={SEARCH_SETTINGS['Count']}&token={TOKEN}"  # НЕ ТРОГАТЬ
HEADERS = {"accept": "application/json"}  # Указываем заголовок для корректного ответа от сайта

# Параметры вывода информации в консоль
PRINT_DATA = True  # Выводить данные в консоль (True-да/False-нет)
SHOW_SETTINGS = {
    "Date": True,  # Выводить дату последней записи (True-да/False-нет)
    "Identificator": True,  # Выводить уникальный ID записи (True-да/False-нет)
    "Sugar_Icon": True,  # Выводить иконку уровня сахара (True-да/False-нет)
    "Sugar": True,  # Выводить уровень сахара (True-да/False-нет)
    "Tendency_Icon": True,  # Выводить иконку тенденции сахара (True-да/False-нет)
    "Tendency": True,  # Выводить название тенденции сахара (True-да/False-нет)
    "Insulin": True,  # Выводить данные о подаче инсулина (True-да/False-нет)
    "Battery_Icon": True,  # Выводить иконку заряда батареи (True-да/False-нет)
    "Battery": True,  # Выводить уровень заряда батареи (True-да/False-нет)
}

# Параметры повторных запросов в секундах
TIMEOUT = 60  # Обновление данных раз в 60 секунд

# Имена переменных
NAMES = {
    "Phone": "iPhone 12 mini",  # Название вашего телефона
    "Transmitter": "Bubble Nano",  # Название вашего трансмиттера
    "Pump": "Medtronic 715"  # Название вашей помпы
}

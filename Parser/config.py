#  Параметры подключения к БД
DATABASE = {
    "Path": "database.db",
    "Sugar": "Sugar",
    "Insulin": "Insulin",
    "Device": "Device",
}

#  Параметры отображения сахара
DICT_TENDENCY = {"Flat": "➡️",
                 "FortyFiveUp": "↗️",
                 "SingleUp": "⬆️",
                 "DoubleUp": "⬆️⬆️",
                 "FortyFiveDown": "↘️",
                 "SingleDown": "⬇️",
                 "DoubleDown": "⬇️⬇️",
                 "NOT COMPUTABLE": "❔",
                 "": "❔"
                 }
SUGAR_LEVELS = {
    (0, 3.9): "🔴",
    (4.0, 4.9): "🟡",
    (5.0, 7.4): "🟢",
    (7.4, 10.0): "🟡",
    (10.1, 40.0): "🔴"
}
SUGAR_MMOL = True

#  Параметры парсинга данных
SEARCH_SETTINGS = {
    "Sugar": True,
    "Insulin": True,
    "Device": True,
    "Count": 100000
}
TOKEN = "7qN05rq8P0Nl"
BASE_URL = "sugarkkleytt.nightaps.com"
URL_SUGAR = f"https://{BASE_URL}/api/v1/entries/?count={SEARCH_SETTINGS['Count']}&token={TOKEN}"
URL_INSULIN = f"https://{BASE_URL}/api/v1/treatments/?count={SEARCH_SETTINGS['Count']}&token={TOKEN}"
URL_DEVICE = f"https://{BASE_URL}/api/v1/devicestatus/?count={SEARCH_SETTINGS['Count']}&token={TOKEN}"
HEADERS = {"accept": "application/json"}  # Указываем заголовок для корректного ответа от сайта

# Параметры вывода информации в консоль
PRINT_DATA = True
SHOW_SETTINGS = {
    "Date": True,
    "Identificator": True,
    "Sugar_Icon": True,
    "Sugar": True,
    "Tendency_Icon": True,
    "Tendency": True,
    "Insulin": True,
    "Battery_Icon": True,
    "Battery": True,
}

# Параметры повторных запросов в секундах
TIMEOUT = 60

# Имена переменных
NAMES = {
    "Phone": "iPhone 12 mini",
    "Transmitter": "Bubble Nano",
    "Pump": "Medtronic 715"
}

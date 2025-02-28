import argparse
import sys
import sqlite3
from prettytable import PrettyTable
import time
import parse as pr  # Парсер данных
import config as cfg  # Файл конфигураций


LAST_PRINT_ID = None


def show_data():
    def check_icon_sugar(sugar_result):
        for (low, high), icon in cfg.SUGAR_LEVELS.items():
            if low <= sugar_result <= high:
                return icon
        return "❔"

    def check_icon_battery(level):
        if int(level) > 30:
            return '🟩'
        elif 20 <= int(level) <= 30:
            return '🟨'
        elif int(level) <= 20:
            return '🟥'
        else:
            return '⬜'

    global LAST_PRINT_ID

    # Подключение к БД
    con_read = sqlite3.connect(cfg.DATABASE['Path'])
    cur_read = con_read.cursor()

    # Запросы для получения всех данных для построения GUI-интерфейса
    data_sugar = cur_read.execute(f"SELECT * FROM {cfg.DATABASE['Sugar']} ORDER BY id DESC LIMIT 1").fetchone()
    data_insulin = cur_read.execute(f"SELECT * FROM {cfg.DATABASE['Insulin']} ORDER BY date DESC LIMIT 1").fetchone()
    data_device = cur_read.execute(f"SELECT * FROM {cfg.DATABASE['Device']}").fetchone()

    # Закрытие подключения к БД
    con_read.close()

    # Строка с датой и идентификатором записи
    date = f"{data_sugar[1]} " if cfg.SHOW_SETTINGS['Date'] else ""
    identificator = f"{data_sugar[0]} " if cfg.SHOW_SETTINGS['Identificator'] else ""

    # Остановка при вывода при совпадении с предыдущим выводом
    if identificator == LAST_PRINT_ID:
        return

    # Строка с уровнем глюкозы в крови (Показатель, цвет, тенденция, изменения)
    sugar_icon = f"{check_icon_sugar(round(float(data_sugar[2]), 1))} " if cfg.SHOW_SETTINGS['Sugar_Icon'] else ""
    sugar = f"{data_sugar[2]} " if cfg.SHOW_SETTINGS['Sugar'] else ""
    tendency = f"{data_sugar[4]} " if cfg.SHOW_SETTINGS['Tendency'] else ""
    tendency_icon = "❔"
    if data_sugar[3] == 'NOT COMPUTABLE' or data_sugar[3] == '' and cfg.SHOW_SETTINGS['Tendency_Icon']:
        tendency_int = abs(float(data_sugar[4]))
        print('Калькулированный расчет тенденции')
        if 0.3 >= tendency_int >= -0.3:
            tendency_icon = "➡️"
        elif 0.6 >= tendency_int > 0.3:
            tendency_icon = "↗️"
        elif 0.9 >= tendency_int > 0.6:
            tendency_icon = "⬆️️"
        elif tendency_int > 0.9:
            tendency_icon = "⬆️⬆️"
        elif -0.6 <= tendency_int < -0.3:
            tendency_icon = "↘️"
        elif -0.9 <= tendency_int < -0.6:
            tendency_icon = "⬇️"
        elif tendency_int < -0.9:
            tendency_icon = "⬇️"
    else:
        tendency_icon = f"{cfg.DICT_TENDENCY[data_sugar[3]]} " if cfg.SHOW_SETTINGS['Tendency_Icon'] else ""

    # Строка с состоянием устройств (Заряд, объем, названия)
    battery_icon_pump = f"{check_icon_battery(data_device[4])} " if cfg.SHOW_SETTINGS['Battery_Icon'] else ""
    battery_icon_iaps = f"{check_icon_battery(data_device[2])} " if cfg.SHOW_SETTINGS['Battery_Icon'] else ""
    battery_icon_transmitter = f"{check_icon_battery(data_device[3])} " if cfg.SHOW_SETTINGS['Battery_Icon'] else ""
    cartridge_pump_icon = f"{check_icon_battery(data_device[5] / 3)}" if cfg.SHOW_SETTINGS['Battery_Icon'] else ""
    battery_pump = f"{data_device[4]}% " if cfg.SHOW_SETTINGS['Battery'] else ""
    battery_iaps = f"{data_device[2]}% " if cfg.SHOW_SETTINGS['Battery'] else ""
    battery_transmitter = f"{data_device[3]}% " if cfg.SHOW_SETTINGS['Battery'] else ""
    cartridge_pump = f"{data_device[5]}U " if cfg.SHOW_SETTINGS['Battery'] else ""
    phone_name = f"{data_device[10]}"
    transmitter_name = f"{data_device[11]}"
    pump_name = f"{data_device[9]}"

    # Строка с последними событиями сделанными помпой
    if cfg.SHOW_SETTINGS['Insulin']:
        base_insulin = f"Base {data_insulin[2]} " if data_insulin[2] != 'None' else "Base 0.00"
        injection_insulin = f"Injection {data_insulin[3]} " if data_insulin[3] != 'None' else "Injection 0.0"
        carbs_insulin = f"Carbs {data_insulin[4]} " if data_insulin[4] != 'None' else "Carbs 0.0"
        if data_insulin[5]:
            duration_insulin = f"{data_insulin[5]}min"
        else:
            duration_insulin = '0min'
    else:
        base_insulin = ""
        injection_insulin = ""
        carbs_insulin = ""
        duration_insulin = ""

    # Создание автоматической таблицы, добавление данных, вывод таблицы в консоль
    table = PrettyTable()

    table.field_names = [
        f"{data_device[1]}",
        f"{data_insulin[1]}.",
        f"{date}"
    ]
    table.add_row([
        f"{phone_name} {battery_icon_iaps}{battery_iaps}",
        f"{base_insulin}",
        f"{sugar_icon}{sugar}"
    ])
    table.add_row(["-------------------------", "-------------------------", "-------------------------"])
    table.add_row([
        f"{transmitter_name} {battery_icon_transmitter}{battery_transmitter}",
        f"{injection_insulin}",
        f"{tendency_icon}-{data_sugar[3]}"
    ])
    table.add_row(["-------------------------", "-------------------------", "-------------------------"])
    table.add_row([
        f"{pump_name} {battery_icon_pump}{battery_pump}",
        f"{carbs_insulin}",
        f"{tendency}"
    ])
    table.add_row(["-------------------------", "-------------------------", "-------------------------"])
    table.add_row([
        f"🍶 {cartridge_pump}{cartridge_pump_icon} {int(int(data_device[5]) / 3)}%",
        f"{duration_insulin}",
        f"{identificator}"
    ])

    print(table, "\n")

    LAST_PRINT_ID = identificator


def loop():
    info_table = PrettyTable()
    info_table.field_names = ['command', 'description']
    info_table.add_row(['/parse', 'Update data from API NightScout'])
    info_table.add_row(['/parse/loop', 'Parse data in loop and print results'])
    info_table.add_row(['/print', 'Print last data'])
    info_table.add_row(['/info', 'Show this table commands'])
    info_table.add_row(['/stop', 'Stop the program'])
    print(info_table, "\n")

    parser = argparse.ArgumentParser(description="Process commands for Diabetes program")
    parser.add_argument(
        "command",
        help="Command to execute",
        nargs="?",  # Сделать аргумент необязательным
        default="/none_args",  # Указать значение по умолчанию, если аргумент отсутствует
        choices=["/parse", "/parse/loop", "/print", "/info", "/stop", "/none_args"]
    )

    args = parser.parse_args()

    if args.command == "/parse":
        results = pr.start()
        print(f"\tРезультат парсинга данных: Sugar - [{results['sugar']}], Insulin - [{results['insulin']}], "
              f"Device - [{results['device']}]")
    elif args.command == "/parse/loop":
        print('\tЗапуск цикла...\n')
        while True:
            pr.start()
            show_data()

            time.sleep(cfg.TIMEOUT)
    elif args.command == "/print":
        show_data()
    elif args.command == "/info":
        print(info_table, "\n")
    elif args.command == "/stop":
        print("Stopping program...")
        sys.exit()
    elif args.command == "/none_args":
        while True:
            query = str(input('Input command: '))
            match query:
                case "/parse":
                    results = pr.start()
                    try:
                        print(
                            f"\tРезультат парсинга данных: "
                            f"Sugar - [{results['sugar']}], "
                            f"Insulin - [{results['insulin']}], "
                            f"Device - [{results['device']}]")
                    except Exception as ex:
                        print(f'Error in PARSE in function run.loop - {ex}')
                case "/parse/loop":
                    print('\tЗапуск цикла...\n')
                    while True:
                        pr.start()
                        try:
                            show_data()
                        except Exception as ex:
                            print(f'Не удалось вывести информацию. Error in module show_data: {ex}')
                        time.sleep(cfg.TIMEOUT)
                case "/print":
                    try:
                        show_data()
                    except Exception as ex:
                        print(f'Не удалось вывести информацию. Error in module show_data: {ex}')
                case "/info":
                    print(info_table, "\n")
                case "/stop":
                    exit(0)
                case _:
                    print('\tError command')
    else:
        print('\tError command')


if __name__ == "__main__":
    loop()

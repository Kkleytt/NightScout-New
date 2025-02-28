import datetime
import time
import requests
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import os
import config as cfg


def search_data():
    def fetch_data(url, headers):
        """Функция для получения данных с сервера"""
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else []

    def process_sugar_data(data_sugar):
        """Обработка данных сахара"""
        return [
            [
                (datetime.datetime.strptime(entry['dateString'], "%Y-%m-%dT%H:%M:%S.%fZ")
                 + datetime.timedelta(hours=3)).strftime("%Y-%m-%d-%H-%M"),
                round(int(entry['sgv']) / 18, 1) if cfg.SUGAR_MMOL else entry['sgv'],
                entry.get('device', ''),
                entry.get('direction', '')
            ]
            for entry in data_sugar
            if all(key in entry for key in ['dateString', 'sgv'])  # Проверка существования ключей
        ]

    def process_insulin_data(data_insulin):
        """Обработка данных инсулина"""
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

    def process_device_data(data_device):
        """Обработка данных устройства"""
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

        device_data['pump_model'] = cfg.NAMES['Pump']
        device_data['phone_model'] = cfg.NAMES['Phone']
        device_data['transmitter_model'] = cfg.NAMES['Transmitter']

        return device_data

    """Основная функция для поиска данных"""
    urls = {
        "sugar": cfg.URL_SUGAR if cfg.SEARCH_SETTINGS['Sugar'] else None,
        "insulin": cfg.URL_INSULIN if cfg.SEARCH_SETTINGS['Sugar'] else None,
        "device": cfg.URL_DEVICE if cfg.SEARCH_SETTINGS['Sugar'] else None
    }

    all_data = {}
    with ThreadPoolExecutor() as executor:
        # Выполняем запросы параллельно
        results = {key: executor.submit(fetch_data, url, cfg.HEADERS) for key, url in urls.items() if url}

        # Обрабатываем результаты запросов
        if cfg.SEARCH_SETTINGS['Sugar']:
            all_data["sugar"] = process_sugar_data(results["sugar"].result())
        if cfg.SEARCH_SETTINGS['Insulin']:
            all_data["insulin"] = process_insulin_data(results["insulin"].result())
        if cfg.SEARCH_SETTINGS['Device']:
            all_data["device"] = process_device_data(results["device"].result())

    return all_data


def write_data_to_db(sugars, insulins, devices):
    def generate_new_id(str_identificator):
        new_int_id = int(str(str_identificator).replace(":", "")) + 1
        new_str_id = f"{'0' * (12 - len(str(new_int_id)))}{str(new_int_id)}"
        return f"{new_str_id[0:4]}:{new_str_id[4:8]}:{new_str_id[8:12]}"

    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, cfg.DATABASE['Path'])
    con_write = sqlite3.connect(db_path)
    cur_write = con_write.cursor()
    all_data = search_data()

    results = {}

    '''Сохранение данных о замерах сахара'''
    try:
        if sugars:
            data = cur_write.execute(f"SELECT id, date, sugar "
                                     f"FROM {cfg.DATABASE['Sugar']} "
                                     f"ORDER BY date DESC LIMIT 2").fetchall()
            last_data_dt = datetime.datetime.strptime(data[0][1], "%Y-%m-%d-%H-%M")
            preview_sugar = data[0][2]
            sug_id = data[0][0]
            for item in reversed(all_data['sugar']):
                new_id = generate_new_id(sug_id)

                item_date_dt = datetime.datetime.strptime(item[0], "%Y-%m-%d-%H-%M")
                if item_date_dt > last_data_dt:
                    query = f"INSERT INTO {cfg.DATABASE['Sugar']} VALUES (?, ?, ?, ?, ?)"
                    difference = round(item[1] - preview_sugar, 1)
                    difference = str(difference) if difference <= 0 else f"+{difference}"
                    preview_sugar = item[1]
                    sug_id = new_id
                    cur_write.execute(query, (new_id, item[0], item[1], item[3], difference))

            con_write.commit()
        results['sugar'] = True
    except Exception as ex:
        print(f"Error in module <write_data> in block <sugars> - {ex}")
        con_write.rollback()  # Откат изменений в БД

    '''Сохранение данных о вводах инсулина | еды'''
    try:
        if insulins:
            ins_id, date = cur_write.execute(f"SELECT id, date "
                                             f"FROM {cfg.DATABASE['Insulin']} "
                                             f"ORDER BY date DESC LIMIT 1").fetchone()
            last_data_dt = datetime.datetime.strptime(date, "%Y-%m-%d-%H-%M")

            for item in reversed(all_data['insulin']):
                new_id = generate_new_id(ins_id)

                item_date_dt = datetime.datetime.strptime(item[0], "%Y-%m-%d-%H-%M")
                if item_date_dt >= last_data_dt:
                    if item_date_dt == last_data_dt:
                        lat = cur_write.execute(f"SELECT base, insulin, carbs, duration "
                                                f"FROM {cfg.DATABASE['Insulin']} "
                                                f"WHERE id = '{ins_id}'").fetchone()
                        lat = list(lat)
                        new_data = [item[1], item[2], item[3], item[4]]
                        if lat != new_data:
                            query = f"INSERT INTO {cfg.DATABASE['Insulin']} VALUES (?, ?, ?, ?, ?, ?, ?)"
                            cur_write.execute(query,
                                              (new_id, item[0], item[1], item[2], item[3], item[4], item[5]))
                            ins_id = new_id
                    else:
                        query = f"INSERT INTO {cfg.DATABASE['Insulin']} VALUES (?, ?, ?, ?, ?, ?, ?)"
                        cur_write.execute(query, (new_id, item[0], item[1], item[2], item[3], item[4], item[5]))
                        ins_id = new_id

            con_write.commit()
        results['insulin'] = True
    except Exception as ex:
        print(f"Error in module <write_data> in block <insulin> - {ex}")
        con_write.rollback()  # Откат изменений в БД

    '''Сохранение данных о устройствах'''
    try:
        if devices:
            query = f"""
                UPDATE {cfg.DATABASE['Device']}
                SET 
                    date = ?,
                    phone_battery = ?, 
                    transmitter_battery = ?,
                    pump_battery = ?,
                    pump_cartridge = ?, 
                    pump_model = ?,
                    phone_model = ?,
                    transmitter_model = ?
                WHERE id = 0;
            """
            cur_write.execute(query, (
                all_data['device']['date'],
                all_data['device']['battery_phone'],
                all_data['device']['battery_transmitter'],
                all_data['device']['battery_pump'],
                all_data['device']['cartridge_pump'],
                all_data['device']['pump_model'],
                all_data['device']['phone_model'],
                all_data['device']['transmitter_model']
            ))

            con_write.commit()
        results['device'] = True
    except Exception as ex:
        print(f"Error in module <write_data> in block <devices> - {ex}")
        con_write.rollback()  # Откат изменений в БД

    # Закрытие соединения с БД
    con_write.close()

    return results


def start():
    try:
        return write_data_to_db(cfg.SEARCH_SETTINGS['Sugar'],
                                cfg.SEARCH_SETTINGS['Insulin'],
                                cfg.SEARCH_SETTINGS['Device'])
    except Exception as ex:
        print(f'Error in function parser.start - {ex}')
        return False


def loop():
    while True:
        try:
            write_data_to_db(cfg.SEARCH_SETTINGS['Sugar'],
                             cfg.SEARCH_SETTINGS['Insulin'],
                             cfg.SEARCH_SETTINGS['Device'])
        except Exception as ex:
            print(f'Error in LOOP in function parser.loop - {ex}')
        time.sleep(cfg.TIMEOUT)


if __name__ == "__main__":
    start()

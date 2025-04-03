## Структура таблиц Базы Данных MySQL:

```
Sugar
├── id [INT]
├── date [INT]
├── value
├── tendency [STR]
└── difference
```

```
**Insulin**
├── id [INT]
├── date [INT]
├── value [FLOAT]
├── carbs [FLOAT]
├── duration [INT]
└── type [STR]
```

```
Device
├── id [INT]
├── date [INT]
├── phone_battery [INT]
├── transmitter_battery [INT]
├── pump_battery [INT]
├── pump_cartridge [INT]
├── insulin_date [INT]
├── cannula_date [INT]
├── sensor_date [INT]
├── pump_name [STR]
├── phone_name [STR]
├── transmitter_name [STR]
├── insulin_name [STR]
└── sensor_name [STR]
```

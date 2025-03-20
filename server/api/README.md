# Структура запросов API-сервера
``` api
API
├── GET
│   ├── /get/sugar/id/token={token}&id={id} - Получение записи сахара по идентификатора
│   ├── /get/sugar/date/token={token}&start={date_start}&end={date_end} - Получение списка записей сахара в промежутке дат
│   ├── /get/sugar/last/token={token} - Получение последней записи сахара
│   ├── /get/insulin/id/token={token}&id={id}- Получение записи инсулина по идентификатора
│   ├── /get/insulin/date/token={token}&start={date_start}&end={date_end} - Получение списка записей инсулина в промежутке дат
│   ├── /get/insulin/last/token={token} - Получение последней записи инсулина
│   └── /get/device/last/token={token} - Получение последней записи устройств
├── POST
│   └── /post/device/token={token} - Обновление записи о устройствах
├── PUT
│   ├── /put/command/token={token} - Отправка нетипичного запроса к БД
│   ├── /put/sugar/token={token} - Добавление новой записи сахара
│   ├── /put/insulin/token={token} - Добавление новой записи инсулина
│   └── /put/device/token={token} - Добавление новой записи устройств
└── DELETE
```
token - Уникальный пароль API-сервера, для верификации запросов

id - Уникальный идентификатор записи

date_start - Дата начала поиска записей

date_end - Дата окончания поиска записей

from pydantic import BaseModel
from typing import Optional


# Структура Таблицы Sugar
class SugarData(BaseModel):
    id: int
    date: int
    value: float
    tendency: str
    difference: float


# Структура Таблицы Insulin
class InsulinData(BaseModel):
    id: int
    date: int
    value: float
    carbs: float
    duration: int
    type: str


# Структура Таблицы Device
class DeviceData(BaseModel):
    id: int
    date: int
    phone_battery: int
    transmitter_battery: int
    pump_battery: int
    pump_cartridge: int
    insulin_date: int
    cannula_date: int
    sensor_date: int
    pump_name: str
    phone_name: str
    transmitter_name: str
    insulin_name: str
    sensor_name: str


# Структура кастомных SQL запросов через API
class CommandData(BaseModel):
    query: str
    params: list


# Структура передачи токена клиенту
class Token(BaseModel):
    access_token: str
    token_type: str


# Структура проверки валидации токена
class TokenData(BaseModel):
    username: Optional[str] = None


# Структура данных пользователя
class User(BaseModel):
    username: str
    password: str

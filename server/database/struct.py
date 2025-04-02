from pydantic import BaseModel
from typing import Optional


# Структура Таблицы Sugar
class SugarData(BaseModel):
    id: str
    date: str
    sugar: float
    tendency: str
    difference: str


# Структура Таблицы Insulin
class InsulinData(BaseModel):
    id: str
    date: str
    insulin: Optional[float] = None
    carbs: Optional[float] = None
    duration: Optional[str] = None
    type: Optional[str] = None


# Структура Таблицы Device
class DeviceData(BaseModel):
    id: int
    date: str
    phone_battery: int
    transmitter_battery: int
    pump_battery: int
    pump_cartridge: float
    cannula: Optional[str] = None
    insulin: Optional[str] = None
    sensor: Optional[str] = None
    pump_model: str
    phone_model: str
    transmitter_model: str


# Структура других запросов
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

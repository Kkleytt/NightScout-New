@echo off
setlocal

REM Перейти в папку приложения
cd /d "%~dp0app"

REM Проверить наличие виртуального окружения
if not exist venv (
    echo Ошибка: Виртуальное окружение не найдено.
    echo Создайте его с помощью команды: python -m venv venv
    pause
    exit /b 1
)

REM Активировать виртуальное окружение
call venv\Scripts\activate.bat

REM Запустить приложение
venv\Scripts\python.exe main.py --printLoop

pause
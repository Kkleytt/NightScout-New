@echo off
:: Устанавливаем кодировку консоли
chcp 65001 >nul

:: Путь к Python, если он не прописан в PATH
set PYTHON_PATH=python

:: Запуск программы с передачей команды
%PYTHON_PATH% run.py /parse/loop

:: Пауза для предотвращения закрытия окна консоли
pause

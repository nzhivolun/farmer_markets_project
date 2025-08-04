@echo off
REM =======================================
REM Запуск проекта Farmer Markets (Windows)
REM =======================================

echo Запуск Docker Compose...
docker-compose up --build -d
IF %ERRORLEVEL% NEQ 0 (
    echo Ошибка запуска docker-compose.
    pause
    exit /b
)

echo Ожидание запуска контейнера farmer_app...
timeout /t 10

REM Проверяем, что контейнер farmer_app работает
docker ps --format "{{.Names}}" | findstr /C:"farmer_app" >nul
IF %ERRORLEVEL% NEQ 0 (
    echo Ошибка: контейнер farmer_app не найден.
    docker ps
    pause
    exit /b
)

echo Запускаем консольное меню...
docker exec -it farmer_app python -m app.main

pause

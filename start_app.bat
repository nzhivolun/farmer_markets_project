@echo off
echo ======================================
echo Запуск приложения Farmer Markets...
echo ======================================

REM Проверка Docker
docker --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Docker не найден! Установите Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b
)

REM Сборка и запуск контейнеров
echo Сборка и запуск контейнеров...
docker-compose up --build -d
IF %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА: Не удалось запустить контейнеры!
    exit /b 1
)

REM Ждём запуск БД
echo Ожидаем запуск базы данных...
timeout /t 15 /nobreak >nul

REM Запускаем приложение в контейнере
echo "Запуск приложения..."
docker exec -it farmer_app python -m app.main  REM -m делает так, что Python считает app пакетом.
REM docker exec -it — запускает команду внутри работающего контейнера.
REM farmer_app — это имя контейнера (задано в docker-compose.yml).
REM python app.main — запускаем наш консольный интерфейс. Конструкция сделана именно так, потому что папка app определена как модуль

IF %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА: Не удалось запустить приложение!
    exit /b 1
)

pause

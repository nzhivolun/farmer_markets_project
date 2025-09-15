@echo off
REM ===========================================================
REM start_app-streamlit.bat
REM Запуск проекта с интерфейсом Streamlit через Docker
REM Логика:
REM 1) Проверяем docker и docker-compose
REM 2) Поднимаем контейнеры (с пересборкой, чтобы подхватить streamlit)
REM 3) Ждём старт БД
REM 4) Запускаем Streamlit ВНУТРИ контейнера через "python -m streamlit"
REM    и биндим на 0.0.0.0, чтобы страница была доступна с хоста.
REM ===========================================================

echo ======================================
echo Запуск приложения Farmer Markets (Streamlit)...
echo ======================================

REM --- Проверяем наличие Docker ---
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo Ошибка: Docker не найден! Установите Docker Desktop: https://docs.docker.com/get-docker/
    pause
    exit /b
)

REM --- Проверяем наличие docker-compose ---
where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo Ошибка: docker-compose не найден! Установите: https://docs.docker.com/compose/install/
    pause
    exit /b
)

REM --- Сборка и запуск контейнеров (ВАЖНО: --build, чтобы в образ попал streamlit) ---
echo Сборка и запуск контейнеров...
docker-compose up --build -d
if %errorlevel% neq 0 (
    echo Ошибка при запуске docker-compose.
    pause
    exit /b
)

REM --- Ждём старт базы (простая пауза) ---
echo Ожидание запуска базы данных...
timeout /t 15 /nobreak >nul

REM --- Проверяем, что контейнер приложения запущен (имя должно быть farmer_app) ---
for /f "tokens=*" %%i in ('docker ps --format "{{.Names}}" ^| findstr /i "farmer_app"') do set APP_NAME=%%i
if "%APP_NAME%"=="" (
    echo Ошибка: контейнер farmer_app не найден или не запущен!
    docker ps
    pause
    exit /b
)

REM --- Запуск Streamlit внутри контейнера ---
REM Используем "python -m streamlit", чтобы не зависеть от PATH.
REM Файл приложения: app/app_streamlit.py
REM ВАЖНО: address=0.0.0.0, чтобы слушать все интерфейсы внутри контейнера,
REM        порт 8501 должен быть проброшен в docker-compose (8501:8501).
echo Запуск Streamlit-приложения...
docker exec -it %APP_NAME% python -m streamlit run app/app_streamlit.py --server.address=0.0.0.0 --server.port=8501

echo.
echo Открой в браузере: http://127.0.0.1:8501
pause

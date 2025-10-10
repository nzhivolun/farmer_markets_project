@echo off
REM ===========================================================
REM start_app-django.bat
REM Простой кросс-платформенный запуск через Docker Compose.
REM На Windows запускаем этот .bat, на Linux/macOS – .sh версию.
REM ===========================================================

setlocal enabledelayedexpansion

echo ================================================
echo [1/6] Проверка Docker/Compose
echo ================================================
where docker >nul 2>nul || (echo [ОШИБКА] Docker не найден. Установи Docker Desktop. & pause & exit /b 1)
docker compose version >nul 2>nul || (echo [ОШИБКА] "docker compose" недоступен. Обнови Docker Desktop. & pause & exit /b 1)

echo ================================================
echo [2/6] Валидация docker-compose.yml
echo ================================================
docker compose config >nul 2>nul || (echo [ОШИБКА] Некорректный docker-compose.yml & pause & exit /b 1)

echo ================================================
echo [3/6] Сборка образов
echo ================================================
docker compose build

echo ================================================
echo [4/6] Запуск БД (service: farmer_db)
echo ================================================
docker compose up -d farmer_db
IF ERRORLEVEL 1 (echo [ОШИБКА] Не удалось запустить farmer_db & pause & exit /b 1)

echo Ожидание старта БД (10 секунд)...
timeout /t 10 >nul

echo ================================================
echo [5/6] Запуск Django (service: farmer_django)
echo ================================================
REM ВАЖНО: имя сервиса должно совпадать с docker-compose.yml
docker compose up -d farmer_django
IF ERRORLEVEL 1 (echo [ОШИБКА] Не удалось запустить сервис farmer_django. Проверь имя сервиса в docker-compose.yml. & pause & exit /b 1)

echo ================================================
echo [6/6] Готово. Логи Django (Ctrl+C чтобы выйти из логов)
echo ================================================
docker compose logs -f farmer_django

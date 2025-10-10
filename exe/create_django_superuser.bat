@echo off
REM ---------------------------------------------------------------
REM create_django_superuser.bat — МИНИМАЛЬНЫЙ СКРИПТ
REM Задача: зайти в УЖЕ ЗАПУЩЕННЫЙ контейнер Django и запустить
REM интерактивный мастер: python /app/web/manage.py createsuperuser
REM ---------------------------------------------------------------

REM 1) Всегда работаем из папки, где лежит этот .bat
cd /d "%~dp0"

REM 2) Имя сервиса из docker-compose.yml. Если у тебя другое — ПОДСТАВЬ.
set "DJANGO_SERVICE=farmer_django"

REM 3) Запускаем интерактивный мастер создания суперпользователя внутри контейнера.
REM    ВАЖНО: путь к manage.py берём из entrypoint.sh — /app/web/manage.py
docker compose exec -it %DJANGO_SERVICE% sh -lc "python /app/web/manage.py createsuperuser"

REM 4) Держим окно открытым, чтобы увидеть ошибки, если они были.
pause

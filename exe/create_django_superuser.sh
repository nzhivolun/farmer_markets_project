#!/usr/bin/env bash
# ---------------------------------------------------------------
# create_django_superuser.sh — МИНИМАЛЬНЫЙ СКРИПТ
# Задача: зайти в УЖЕ ЗАПУЩЕННЫЙ контейнер Django и запустить
# интерактивный мастер: python /app/web/manage.py createsuperuser
# ---------------------------------------------------------------

set -euo pipefail
IFS=$'\n\t'

# 1) Всегда работаем из папки, где лежит этот .sh
cd "$(dirname "$0")"

# 2) Имя сервиса из docker-compose.yml. Если у тебя другое — ПОДСТАВЬ.
DJANGO_SERVICE="farmer_django"

# 3) Запускаем интерактивный мастер создания суперпользователя внутри контейнера.
#    ВАЖНО: путь к manage.py берём из entrypoint.sh — /app/web/manage.py
docker compose exec -it "$DJANGO_SERVICE" sh -lc "python /app/web/manage.py createsuperuser"

# 4) Держим окно открытым, чтобы увидеть ошибки (в Linux нет pause, но добавим подсказку).
echo
read -rp "Нажми Enter, чтобы закрыть..."

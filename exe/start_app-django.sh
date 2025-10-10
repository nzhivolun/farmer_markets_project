#!/usr/bin/env bash
# ===========================================================
# start_app-django.sh
# Простой кросс-платформенный запуск через Docker Compose.
# На Linux/macOS — версия под bash.
# ===========================================================

set -euo pipefail  # Останавливаем скрипт при ошибке
IFS=$'\n\t'

echo "==============================================="
echo "[1/6] Проверка Docker/Compose"
echo "==============================================="

# Проверяем наличие docker
if ! command -v docker &>/dev/null; then
  echo "[ОШИБКА] Docker не найден. Установи Docker."
  exit 1
fi

# Проверяем наличие docker compose
if ! docker compose version &>/dev/null; then
  echo '[ОШИБКА] "docker compose" недоступен. Обнови Docker.'
  exit 1
fi

echo "==============================================="
echo "[2/6] Валидация docker-compose.yml"
echo "==============================================="

if ! docker compose config &>/dev/null; then
  echo "[ОШИБКА] Некорректный docker-compose.yml"
  exit 1
fi

echo "==============================================="
echo "[3/6] Сборка образов"
echo "==============================================="
docker compose build

echo "==============================================="
echo "[4/6] Запуск БД (service: farmer_db)"
echo "==============================================="
if ! docker compose up -d farmer_db; then
  echo "[ОШИБКА] Не удалось запустить farmer_db"
  exit 1
fi

echo "Ожидание старта БД (10 секунд)..."
sleep 10

echo "==============================================="
echo "[5/6] Запуск Django (service: farmer_django)"
echo "==============================================="
if ! docker compose up -d farmer_django; then
  echo "[ОШИБКА] Не удалось запустить сервис farmer_django. Проверь имя сервиса в docker-compose.yml."
  exit 1
fi

echo "==============================================="
echo "[6/6] Готово. Логи Django (Ctrl+C чтобы выйти из логов)"
echo "==============================================="
docker compose logs -f farmer_django

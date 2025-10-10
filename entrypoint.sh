#!/bin/bash
# ===========================================================
# entrypoint.sh — единая логика старта контейнера
# Работает и для Streamlit, и для Django.
# ===========================================================

set -e  # при любой ошибке завершаем скрипт

echo "[entrypoint] Ждём запуск PostgreSQL..."
sleep 10
# Небольшая пауза нужна, чтобы Postgres точно успел подняться.

# 1) ВСЕГДА прогоняем миграции Django.
#    Это важно даже в режиме Streamlit, потому что наша схема (init.sql)
#    использует внешние ключи на таблицу auth_user (создаётся миграциями).
echo "[entrypoint] Выполняем миграции Django (создадут auth_user и прочие служебные таблицы)..."
python /app/web/manage.py migrate

# 2.1) Инициализируем группы и права (идемпотентно, безопасно при повторах)
echo "[entrypoint] Инициализируем роли (группы и права)..."
python /app/web/manage.py init_roles || echo "[entrypoint] [⚠] init_roles завершилась с предупреждением — продолжаем."


# 2) Инициализация пользовательской схемы (наши таблицы markets/locations/...).
echo "[entrypoint] Инициализация базы (setup_db.py)..."
python /app/setup/setup_db.py

# 3) Загрузка данных из CSV (если файл и скрипт существуют).
if [ -f /app/app/load_data.py ]; then
  echo "[entrypoint] Загружаем данные из CSV..."
  python /app/app/load_data.py
else
  echo "[entrypoint] [⚠] Файл /app/app/load_data.py не найден — пропускаем загрузку данных."
fi

# 4) Запуск приложения по режиму.
if [ "${APP_MODE}" = "django" ]; then
  echo "[entrypoint] Запуск Django..."

  # ---------------------------------------------
  # Подсказка в логах: куда заходить в браузере
  # ---------------------------------------------
  echo ""
  echo "================================================"
  echo "Открыть сайт:  http://127.0.0.1:8502/"
  echo "Админка:       http://127.0.0.1:8502/admin/"
  echo "================================================"
  echo ""

  # (Опционально) Создать суперпользователя из ENV
  if [ -n "${DJANGO_SUPERUSER_USERNAME}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ]; then
    echo "[entrypoint] Создаю суперпользователя ${DJANGO_SUPERUSER_USERNAME} (если его ещё нет)..."
    python /app/web/manage.py createsuperuser \
      --noinput \
      --username "${DJANGO_SUPERUSER_USERNAME}" \
      --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" \
      || echo "[entrypoint] Суперпользователь уже существует — пропускаем создание."
  else
    echo "[entrypoint] Переменные DJANGO_SUPERUSER_USERNAME/PASSWORD не заданы — пропускаю автосоздание суперпользователя."
  fi

  exec python /app/web/manage.py runserver 0.0.0.0:8502 --insecure
else
  echo "[entrypoint] Запуск Streamlit..."

  # Для полноты — подсказка и для Streamlit-режима
  echo ""
  echo "================================================"
  echo "Открыть сайт:  http://127.0.0.1:8501/"
  echo "================================================"
  echo ""

  exec streamlit run /app/app/app_streamlit.py --server.port=8501 --server.address=0.0.0.0
fi

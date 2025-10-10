#!/bin/bash
# ===========================================================
# start_app-streamlit.sh
#
# Скрипт запуска Streamlit-версии приложения на Linux/macOS.
# ===========================================================

echo "======================================"
echo "Запуск Streamlit приложения Farmer Markets..."
echo "======================================"

# --- Проверка наличия Docker ---
if ! command -v docker &> /dev/null; then
    echo "Docker не найден! Установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose не найден! Установите: https://docs.docker.com/compose/install/"
    exit 1
fi

# --- Запускаем контейнеры ---
echo "Сборка и запуск контейнеров..."
docker-compose up --build -d

# --- Ждём запуск базы данных ---
echo "Ожидание запуска базы данных..."
sleep 15

# --- Проверяем, что контейнер farmer_app запущен ---
if ! docker ps --format '{{.Names}}' | grep -q 'farmer_app'; then
    echo "Ошибка: контейнер farmer_app не запущен!"
    exit 1
fi

# --- Запуск Streamlit внутри контейнера ---
echo "Откройте в браузере: http://127.0.0.1:8501"
docker exec -it farmer_app streamlit run app/app_streamlit.py --server.port=8501 --server.address=0.0.0.0 --browser.serverAddress=127.0.0.1 --browser.serverPort=8501

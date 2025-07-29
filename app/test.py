import sys 
import os

# === Добавляем путь к папке setup, чтобы импортировать config.py ===
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))

# # === Импортируем настройки подключения к базе данных ===
# from setup.config import DB_CONFIG

# === Путь к CSV-файлу с исходными данными ===
CSV_FILE = os.path.join(os.path.dirname(__file__), '..', 'setup', 'Export.csv')

with open (CSV_FILE, 'r') as file:
    line = file.readline()
    line = line.split(",")[28:-2]
    print(line)

    
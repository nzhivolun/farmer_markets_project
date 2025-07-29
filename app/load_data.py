# load_data.py
# =======================================================
# Этот скрипт загружает данные из CSV-файла (Export.csv)
# в базу данных PostgreSQL.
#
# Основные шаги:
# 1. Подключение к базе данных.
# 2. Добавление категорий в таблицу categories.
# 3. Добавление локаций, рынков и связей с категориями.
# =======================================================

import sys
import os
import csv
import psycopg2  # библиотека для подключения к PostgreSQL


# === Добавляем путь к папке setup, чтобы импортировать config.py ===
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))

# === Импортируем настройки подключения к базе данных ===
from setup.config import DB_CONFIG 

# === Путь к CSV-файлу с исходными данными ===
CSV_FILE = os.path.join(os.path.dirname(__file__), '..', 'setup', 'Export.csv')

def load_data():
    """
    Загружает данные из Export.csv в PostgreSQL:
    - Создаёт категории (если не созданы)
    - Добавляет рынки, локации
    - Создаёт связи рынок -> категория
    """
    try:
        # 1. Подключаемся к базе данных
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor() # создает курсор: Курсор позволяет выполнять SQL-запросы и получать результаты

        # === Шаг 2. Список категорий (берём из CSV колонок с Y/N) ===
        # categories_list = [
        #     "Bakedgoods", "Cheese", "Crafts", "Flowers", "Eggs", "Seafood",
        #     "Herbs", "Vegetables", "Honey", "Jams", "Maple", "Meat",
        #     "Nursery", "Nuts", "Plants", "Poultry", "Prepared", "Soap",
        #     "Trees", "Wine", "Coffee", "Beans", "Fruits", "Grains",
        #     "Juices", "Mushrooms", "PetFood", "Tofu", "WildHarvested"
        # ]

        # === Шаг 2. Список категорий (берём из CSV колонок с Y/N) ===
        categories_list = []
        with open (CSV_FILE, 'r') as file:
            line = file.readline()
            categories_list = line.split(",")[28:-2]

        # === Шаг 3. Проверяем, есть ли категории в таблице categories ===
        cur.execute("SELECT COUNT(*) FROM categories")
        count = cur.fetchone()[0] 
        """Выполняется SQL-запрос, который подсчитывает количество записей в таблице categories
        fetchone() это метод курсора, получает первую строку результата (в виде кортежа)
        [0] извлекает первый (и единственный) элемент из этого кортежа - собственно число записей
        Это число сохраняется в переменную count
        По сути, этот код отвечает на вопрос: "Сколько всего категорий существует в таблице?"
        Эквивалент на человеческом языке: "Посчитай все записи в таблице categories и скажи мне их количество"."""

        # Если таблица пустая — добавляем все категории
        if count == 0:
            print("Добавляем категории в таблицу categories...")
            for cat in categories_list:
                # Вставляем каждую категорию (например, "Meat") далее по коду будет %s - placeholder (метка-заполнитель), означает, что на это место будет подставлено значение переменной cat. Вроде как защита от SQL-инъекций
                cur.execute("INSERT INTO categories (name) VALUES (%s)", (cat,))
            conn.commit()
            print("Категории добавлены.")
        else:
            print("Категории уже существуют в базе.")

        # === Шаг 4. Открываем CSV-файл для чтения ===
        with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)  # Читаем строки как словарь

            # === Обрабатываем каждую строку (один рынок) ===
            for row in reader:
                # Достаём основные поля
                city = row["city"].strip() if row["city"] else None
                state = row["State"].strip() if row["State"] else None
                street = row["street"].strip() if row["street"] else None
                county = row["County"].strip() if row["County"] else None
                zip_code = row["zip"].strip() if row["zip"] else None

                # Если нет города или штата — пропускаем (невалидная запись)
                if not city or not state:
                    continue

                # === Проверяем, есть ли локация (город + штат + индекс) ===
                cur.execute("""
                    SELECT id FROM locations WHERE city=%s AND state=%s AND zip=%s
                """, (city, state, zip_code))
                loc = cur.fetchone()

                if loc:
                    location_id = loc[0]
                else:
                    # Если локации нет — добавляем новую
                    cur.execute("""
                        INSERT INTO locations (street, city, county, state, zip)
                        VALUES (%s, %s, %s, %s, %s) RETURNING id
                    """, (street, city, county, state, zip_code))
                    location_id = cur.fetchone()[0]

                # === Добавляем рынок в таблицу markets ===
                cur.execute("""
                    INSERT INTO markets (name, location_id, website, facebook, twitter, youtube, other_media, latitude, longitude)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (
                    row["MarketName"], location_id,
                    row["Website"], row["Facebook"], row["Twitter"], row["Youtube"], row["OtherMedia"],
                    float(row["y"]) if row["y"] else None,  # широта
                    float(row["x"]) if row["x"] else None   # долгота
                ))
                market_id = cur.fetchone()[0]

                # === Добавляем связи рынок -> категория ===
                for cat in categories_list:
                    # Если в CSV указано Y, значит категория есть на рынке
                    if row.get(cat) == "Y":
                        # Находим id категории по имени
                        cur.execute("SELECT id FROM categories WHERE name=%s", (cat,))
                        category_id = cur.fetchone()[0]

                        # Вставляем связь в таблицу market_categories
                        cur.execute("""
                            INSERT INTO market_categories (market_id, category_id)
                            VALUES (%s, %s)
                        """, (market_id, category_id))

            # Сохраняем все изменения
            conn.commit()
            print("Данные рынков и категорий загружены в базу.")

        # ОБЯЗАТЕЛЬНО Закрываем соединение
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")


# === Точка входа ===
if __name__ == "__main__":
    load_data()

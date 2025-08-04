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
# Добавляем путь к корню проекта, чтобы корректно работал импорт setup.config при ручном запуске
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import csv
import psycopg2  # библиотека для подключения к PostgreSQL
# === Импортируем настройки подключения к базе данных ===
from setup.config import DB_CONFIG 

# === Путь к CSV-файлу с исходными данными ===
CSV_FILE = os.path.join(os.path.dirname(__file__), '..', 'setup', 'Export.csv')

def normalize(value):
    if value is None:
        return None
    value = str(value).strip()
    if value.startswith("http://"):
        value = value.replace("http://", "https://")
    if value.endswith("/"):
        value = value.rstrip("/")
    return value if value else None


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

        # === Шаг 2. Получаем список категорий из заголовка CSV ===
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            header_line = file.readline().strip()
            columns = header_line.split(",")

            # Категории начинаются с 29-й колонки (индекс 28) и идут до предпоследней
            # Последние две колонки — "y" и "x" (координаты), их исключаем
            categories_list = columns[28:-2]

            # Убираем пробелы и лишние символы (на всякий случай)
            categories_list = [c.strip() for c in categories_list]

            print("Категории из CSV:", categories_list)  # можно временно оставить


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
            missing_categories = set()  # сюда запишем категории, которых нет в таблице
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

                # Приводим значения к нормализованному виду (убираем пробелы, '' → None)
                market_fields = (
                    normalize(row["MarketName"]),
                    location_id,
                    normalize(row["Website"]),
                    normalize(row["Facebook"]),
                    normalize(row["Twitter"]),
                    normalize(row["Youtube"]),
                    normalize(row["OtherMedia"]),
                    float(row["y"]) if row["y"] else None,
                    float(row["x"]) if row["x"] else None
                )

                # Пытаемся вставить рынок
                cur.execute("""
                    INSERT INTO markets (name, location_id, website, facebook, twitter, youtube, other_media, latitude, longitude)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name, location_id, website, facebook, twitter, youtube, other_media, latitude, longitude)
                    DO NOTHING
                    RETURNING id
                """, market_fields)

                result = cur.fetchone()

                if result:
                    market_id = result[0]
                else:
                    # Если рынок уже есть, ищем его ID вручную (учитывая NULL и пробелы)
                    cur.execute("""
                        SELECT id FROM markets
                        WHERE name IS NOT DISTINCT FROM %s
                        AND location_id IS NOT DISTINCT FROM %s
                        AND website IS NOT DISTINCT FROM %s
                        AND facebook IS NOT DISTINCT FROM %s
                        AND twitter IS NOT DISTINCT FROM %s
                        AND youtube IS NOT DISTINCT FROM %s
                        AND other_media IS NOT DISTINCT FROM %s
                        AND latitude IS NOT DISTINCT FROM %s
                        AND longitude IS NOT DISTINCT FROM %s
                    """, market_fields)

                    market_result = cur.fetchone()
                    if market_result:
                        market_id = market_result[0]
                    else:
                        print("Ошибка: рынок не найден, хотя должен быть уникальным. Пропускаем.")
                        print("Данные для поиска:", market_fields)

                        continue



                

                # === Добавляем связи рынок -> категория ===
                for cat in categories_list:
                    if row.get(cat) == "Y":
                        cur.execute("SELECT id FROM categories WHERE name=%s", (cat,))
                        result = cur.fetchone()

                        if result:
                            category_id = result[0]
                            cur.execute("""
                                INSERT INTO market_categories (market_id, category_id)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING
                            """, (market_id, category_id))

                        else:
                            if cat not in missing_categories:
                                print(f"Предупреждение: категория '{cat}' не найдена в таблице.")
                                missing_categories.add(cat)


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

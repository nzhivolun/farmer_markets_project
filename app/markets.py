# markets.py
# ===========================================================
# Функции для работы с рынками:
# - Показ списка рынков
# - Поиск по городу/штату/индексу
# - Детали рынка
# - Сортировка
# - Поиск по радиусу
# - Удаление рынка
# ===========================================================

from .db import execute_query  # работа с БД
from .utils import validate_id, validate_coordinates, paginate  # общие функции

# ===========================================================
# 1. Список рынков с пагинацией
# ===========================================================
def show_markets():
    per_page = 20
    offset = 0

    while True:
        query = """
            SELECT m.id, m.name, l.city, l.state,
                   COALESCE(AVG(r.rating), 0) AS avg_rating,
                   COUNT(r.id) AS review_count
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            LEFT JOIN reviews r ON r.market_id = m.id
            GROUP BY m.id, l.city, l.state
            ORDER BY m.id
            LIMIT %s OFFSET %s
        """
        results = execute_query(query, (per_page, offset), fetch=True)

        if not results:
            offset = paginate(results, offset, per_page)
            if offset is None:
                break
            continue

        print(f"\n=== Список рынков (с {offset + 1} по {offset + len(results)}) ===")
        for r in results:
            print(f"{r['id']}. {r['name']} ({r['city']}, {r['state']}) "
                  f"- Рейтинг: {round(r['avg_rating'], 1)} | Отзывов: {r['review_count']}")

        print("[+] Следующие | [-] Предыдущие | [0] Меню")
        cmd = input("Ваш выбор: ").strip()
        if cmd == "+":
            offset += per_page
        elif cmd == "-":
            offset = max(0, offset - per_page)
        elif cmd == "0":
            break


# ===========================================================
# 2. Поиск по городу/штату/индексу
# ===========================================================
def search_market():
    city = input("Введите город (Enter - пропустить): ").strip()
    state = input("Введите штат (Enter - пропустить): ").strip()
    zip_code = input("Введите индекс (Enter - пропустить): ").strip()

    query = """
        SELECT m.id, m.name, l.city, l.state, l.zip
        FROM markets m
        JOIN locations l ON m.location_id = l.id
        WHERE (%s = '' OR l.city ILIKE %s)
          AND (%s = '' OR l.state ILIKE %s)
          AND (%s = '' OR l.zip = %s)
        LIMIT 20
    """
    params = (city, f"%{city}%", state, f"%{state}%", zip_code, zip_code)
    results = execute_query(query, params, fetch=True)

    if results:
        print("\n=== Результаты поиска ===")
        for r in results:
            print(f"{r['id']}. {r['name']} ({r['city']}, {r['state']} ZIP: {r['zip']})")
    else:
        print("Ничего не найдено.")


# ===========================================================
# 3. Детали рынка + отзывы
# ===========================================================
def show_market_details():
    market_id = validate_id(input("Введите ID рынка: ").strip())
    if market_id is None:
        return

    query = """
        SELECT m.name, l.city, l.state, m.website, m.facebook, m.twitter, m.youtube, m.other_media
        FROM markets m
        JOIN locations l ON m.location_id = l.id
        WHERE m.id = %s
    """
    details = execute_query(query, (market_id,), fetch=True)

    if not details:
        print("Рынок не найден.")
        return

    d = details[0]
    print(f"\nНазвание: {d['name']}")
    print(f"Город: {d['city']}, {d['state']}")
    print(f"Website: {d['website']}")
    print(f"Facebook: {d['facebook']}")
    print(f"Twitter: {d['twitter']}")
    print(f"Youtube: {d['youtube']}")
    print(f"Other: {d['other_media']}")

    print("\nОтзывы:")
    reviews = execute_query("SELECT user_name, rating, review_text FROM reviews WHERE market_id = %s",
                             (market_id,), fetch=True)
    if reviews:
        for r in reviews:
            print(f"{r['user_name']} ({r['rating']}): {r['review_text']}")
    else:
        print("Нет отзывов.")


# ===========================================================
# 4. Сортировка рынков
# ===========================================================
def sort_markets():
    print("\nСортировка по: [1] рейтингу, [2] городу, [3] штату, [4] расстоянию")
    choice = input("Выберите: ").strip()
    direction = "ASC"

    if choice in ["1", "2", "3", "4"]:
        if input("Направление [1] возрастание | [2] убывание: ").strip() == "2":
            direction = "DESC"
    else:
        print("Неверный выбор.")
        return

    per_page = 20
    offset = 0

    if choice == "1":
        order_clause = f"ORDER BY avg_rating {direction}"
        query_template = f"""
            SELECT m.id, m.name, l.city, l.state, COALESCE(AVG(r.rating), 0) AS avg_rating
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            LEFT JOIN reviews r ON r.market_id = m.id
            GROUP BY m.id, l.city, l.state
            {{order}}
            LIMIT %s OFFSET %s
        """
    elif choice == "2":
        order_clause = f"ORDER BY l.city {direction}"
        query_template = f"""
            SELECT m.id, m.name, l.city, l.state
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            {{order}}
            LIMIT %s OFFSET %s
        """
    elif choice == "3":
        order_clause = f"ORDER BY l.state {direction}"
        query_template = f"""
            SELECT m.id, m.name, l.city, l.state
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            {{order}}
            LIMIT %s OFFSET %s
        """
    else:  # если выбрана сортировка по расстоянию
        while True:
            lat = input("Введите широту: ").strip()
            if lat == "0":
                print("Возврат в меню...")
                return
            lon = input("Введите долготу: ").strip()
            if lon == "0":
                print("Возврат в меню...")
                return
            coords = validate_coordinates(lat, lon)
            if coords:
                lat, lon = coords
                break
            else:
                print("Повторите ввод координат.\n")

        order_clause = f"ORDER BY distance {direction}"
        query_template = f"""
            SELECT m.id, m.name, l.city, l.state,
            (3959 * acos(
                cos(radians({lat})) * cos(radians(m.latitude)) *
                cos(radians(m.longitude) - radians({lon})) +
                sin(radians({lat})) * sin(radians(m.latitude))
            )) AS distance
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            {{order}}
            LIMIT %s OFFSET %s
        """


    while True:
        query = query_template.format(order=order_clause)
        results = execute_query(query, (per_page, offset), fetch=True)
        if not results:
            offset = paginate(results, offset, per_page)
            if offset is None:
                break
            continue

        for r in results:
            if "avg_rating" in r:
                print(f"{r['id']}. {r['name']} ({r['city']}, {r['state']}) - Рейтинг: {round(r['avg_rating'], 1)}")
            elif "distance" in r:
                print(f"{r['id']}. {r['name']} ({r['city']}, {r['state']}) - {round(r['distance'], 2)} миль")
            else:
                print(f"{r['id']}. {r['name']} ({r['city']}, {r['state']})")

        cmd = input("[+] Следующие | [-] Предыдущие | [0] Меню: ").strip()
        if cmd == "+":
            offset += per_page
        elif cmd == "-":
            offset = max(0, offset - per_page)
        elif cmd == "0":
            break


# ===========================================================
# 5. Поиск по радиусу (30 миль)
# ===========================================================
def search_by_radius():
    # Бесконечный цикл, пока не введем корректные координаты
    while True:
        lat = input("Введите широту: ").strip()
        lon = input("Введите долготу: ").strip()
        coords = validate_coordinates(lat, lon)
        if coords:  # если координаты корректные
            lat, lon = coords
            break     # выходим из цикла
        else:
            print("Повторите ввод координат.\n")

    # Далее SQL-запрос как было
    query = """
        SELECT m.id, m.name, l.city, l.state,
        (3959 * acos(
            cos(radians(%s)) * cos(radians(m.latitude)) *
            cos(radians(m.longitude) - radians(%s)) +
            sin(radians(%s)) * sin(radians(m.latitude))
        )) AS distance
        FROM markets m
        JOIN locations l ON m.location_id = l.id
        WHERE (3959 * acos(
            cos(radians(%s)) * cos(radians(m.latitude)) *
            cos(radians(m.longitude) - radians(%s)) +
            sin(radians(%s)) * sin(radians(m.latitude))
        )) < 30
        ORDER BY distance ASC
        LIMIT 20
    """
    params = (lat, lon, lat, lat, lon, lat)
    results = execute_query(query, params, fetch=True)

    if results:
        print("\n=== Рынки в радиусе 30 миль ===")
        for r in results:
            print(f"{r['id']}. {r['name']} ({r['city']}, {r['state']}) - {round(r['distance'], 2)} миль")
    else:
        print("Ничего не найдено.")

# ===========================================================
# 6. Удаление рынка
# ===========================================================
def delete_market():
    market_id = validate_id(input("Введите ID рынка: ").strip())
    if market_id is None:
        return

    confirm = input(f"Удалить рынок {market_id}? (y/n): ").strip().lower()
    if confirm == "y":
        execute_query("DELETE FROM markets WHERE id = %s", (market_id,))
        print("Рынок удалён.")
    else:
        print("Удаление отменено.")

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

from .db import execute_query  # импортируем функцию, которая выполняет SQL-запросы
from .utils import validate_id, validate_coordinates, paginate # импортируем функции для проверки ввода и навигации
# ===========================================================
# 1. Список рынков с пагинацией
# ===========================================================
def show_markets():
    per_page = 20 # Кол-во записей на одну страницу
    offset = 0 # Смещение — с какой записи начинать вывод
    
    # Получаем общее количество рынков
    count_query = "SELECT COUNT(*) FROM markets"
    total = execute_query(count_query, fetch=True)[0]['count'] # вытаскиваем число из результата


    while True:
        # SQL-запрос выводит id, имя, город, штат, рейтинг и число отзывов
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
        # Выполняем запрос и получаем результат
        results = execute_query(query, (per_page, offset), fetch=True)

        if not results:
            print("Больше данных нет.")
            break  # выходим в меню

        # Выводим список рынков
        print(f"\n=== Список рынков (с {offset + 1} по {offset + len(results)}) ===")
        for r in results:
            print(f"{r['id']}. {r['name']} ({r['city']}, {r['state']}) "
                  f"- Рейтинг: {round(r['avg_rating'], 1)} | Отзывов: {r['review_count']}")
        # Переход на следующую/предыдущую страницу
        offset = paginate(offset, per_page, total)
        if offset is None:
            break # если пользователь выбрал выход — выходим из цикла


# ===========================================================
# 2. Поиск по городу/штату/индексу
# ===========================================================
def search_market():
    # Ввод от пользователя
    city = input("Введите город (Enter - пропустить): ").strip()
    state = input("Введите штат (Enter - пропустить): ").strip()
    zip_code = input("Введите индекс (Enter - пропустить): ").strip()

    # SQL с параметрами
    base_query = """
        SELECT m.id, m.name, l.city, l.state, l.zip
        FROM markets m
        JOIN locations l ON m.location_id = l.id
        WHERE (%s = '' OR l.city ILIKE %s)
          AND (%s = '' OR l.state ILIKE %s)
          AND (%s = '' OR l.zip = %s)
        ORDER BY m.id
        LIMIT %s OFFSET %s
    """

    # Считаем общее количество подходящих строк
    count_query = """
        SELECT COUNT(*) 
        FROM markets m
        JOIN locations l ON m.location_id = l.id
        WHERE (%s = '' OR l.city ILIKE %s)
          AND (%s = '' OR l.state ILIKE %s)
          AND (%s = '' OR l.zip = %s)
    """

    params = (city, f"%{city}%", state, f"%{state}%", zip_code, zip_code)
    total = execute_query(count_query, params, fetch=True)[0]['count']

    if total == 0:
        print("Ничего не найдено.")
        return

    per_page = 20
    offset = 0

    while True:
        print(f"\n=== Найдено {total} рынков ===")
        query_params = (*params, per_page, offset)
        results = execute_query(base_query, query_params, fetch=True)

        for r in results:
            print(f"{r['id']}. {r['name']} ({r['city']}, {r['state']} ZIP: {r['zip']})")

        offset = paginate(offset, per_page, total)
        if offset is None:
            break


# ===========================================================
# 3. Детали рынка + отзывы
# ===========================================================
def show_market_details():
    # Запрашиваем ID рынка и валидируем его (функция вернёт int или None)
    market_id = validate_id(input("Введите ID рынка: ").strip())
    if market_id is None:
        return # если ID не число — выходим

    # SQL-запрос на получение полной информации о выбранном рынке
    query = """
        SELECT m.name, l.city, l.state, m.website, m.facebook, m.twitter, m.youtube, m.other_media
        FROM markets m
        JOIN locations l ON m.location_id = l.id
        WHERE m.id = %s
    """
    details = execute_query(query, (market_id,), fetch=True)

    if not details:
        print("Рынок не найден.") # если рынок не найден — выходим
        return

    d = details[0] # вытаскиваем первую (и единственную) строку результата

    # Выводим информацию на экран
    print(f"\nНазвание: {d['name']}")
    print(f"Город: {d['city']}, {d['state']}")
    print(f"Website: {d['website']}")
    print(f"Facebook: {d['facebook']}")
    print(f"Twitter: {d['twitter']}")
    print(f"Youtube: {d['youtube']}")
    print(f"Other: {d['other_media']}")

    # Далее — получаем и выводим отзывы
    print("\nОтзывы:")
    reviews = execute_query("SELECT id, user_name, rating, review_text FROM reviews WHERE market_id = %s",
                            (market_id,), fetch=True)

    if reviews:
        for r in reviews:
            user = str(r.get('user_name') or "").strip()
            text = str(r.get('review_text') or "").strip()
            print(f"[{r['id']}] {user} ({r['rating']}): {text}")
    else:
        print("Нет отзывов.")




# ===========================================================
# 4. Сортировка рынков
# ===========================================================
def sort_markets():
    # Предлагаем пользователю выбрать критерий сортировки
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
    
    # Получаем общее количество рынков для правильной пагинации
    total_query = "SELECT COUNT(*) FROM markets"
    total = execute_query(total_query, fetch=True)[0]['count']

    # Вариант сортировки: по рейтингу
    if choice == "1":
        order_clause = f"ORDER BY avg_rating {direction}"
        
        # Используем шаблон SQL-запроса с группировкой по рынкам
        query_template = f"""
            SELECT m.id, m.name, l.city, l.state, COALESCE(AVG(r.rating), 0) AS avg_rating
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            LEFT JOIN reviews r ON r.market_id = m.id
            GROUP BY m.id, l.city, l.state
            {{order}}
            LIMIT %s OFFSET %s
        """
    
    # Сортировка по городу
    elif choice == "2":
        order_clause = f"ORDER BY l.city {direction}"
        query_template = f"""
            SELECT m.id, m.name, l.city, l.state
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            {{order}}
            LIMIT %s OFFSET %s
        """
    
    # Сортировка по штату
    elif choice == "3":
        order_clause = f"ORDER BY l.state {direction}"
        query_template = f"""
            SELECT m.id, m.name, l.city, l.state
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            {{order}}
            LIMIT %s OFFSET %s
        """
        
    # Сортировка по расстоянию — отдельный случай, нужна координата
    else:  
        # Бесконечный цикл — пока не введём корректные координаты
        while True:
            lat = input("Введите широту: ").strip()
            if lat == "0":
                print("Возврат в меню...")
                return
            lon = input("Введите долготу: ").strip()
            if lon == "0":
                print("Возврат в меню...")
                return
            
            coords = validate_coordinates(lat, lon) # проверка корректности координат
            if coords:
                lat, lon = coords
                break
            else:
                print("Повторите ввод координат.\n")

        # Кол-во только тех рынков, у которых есть координаты
        count_query = """
            SELECT COUNT(*) FROM markets
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
        total = execute_query(count_query, fetch=True)[0]['count']

        order_clause = f"ORDER BY distance {direction}"
        
        # В SQL запросе используем формулу Haversine для расчёта расстояния в милях
        query_template = f"""
            SELECT m.id, m.name, l.city, l.state,
            (3959 * acos(
                cos(radians({lat})) * cos(radians(m.latitude)) *
                cos(radians(m.longitude) - radians({lon})) +
                sin(radians({lat})) * sin(radians(m.latitude))
            )) AS distance
            FROM markets m
            JOIN locations l ON m.location_id = l.id
            WHERE m.latitude IS NOT NULL AND m.longitude IS NOT NULL
            {{order}}
            LIMIT %s OFFSET %s
        """

    # Основной цикл вывода отсортированных данных с постраничным просмотром
    while True:
        # Вставляем нужный order_by в шаблон запроса
        query = query_template.format(order=order_clause)
        results = execute_query(query, (per_page, offset), fetch=True)
        if not results:
            print("Больше данных нет.")
            break

        # Выводим рынки с учётом типа сортировки
        for r in results:
            if "avg_rating" in r:
                print(f"{r['id']}. {r['name']} ({r['city']}, {r['state']}) - Рейтинг: {round(r['avg_rating'], 1)}")
            elif "distance" in r:
                print(f"{r['id']}. {r['name']} ({r['city']}, {r['state']}) - {round(r['distance'], 2)} миль")
            else:
                print(f"{r['id']}. {r['name']} ({r['city']}, {r['state']})")

        # Обновляем смещение offset в зависимости от действий пользователя
        offset = paginate(offset, per_page, total)
        if offset is None:
            break



# ===========================================================
# 5. Поиск по радиусу (30 миль)
# ===========================================================
def search_by_radius():
    # Бесконечный цикл — пока пользователь не введёт правильные координаты
    while True:
        lat = input("Введите широту: ").strip()
        lon = input("Введите долготу: ").strip()
        
        # Проверяем координаты на корректность: float + в пределах допустимого диапазона
        coords = validate_coordinates(lat, lon)
        if coords:  
            # Если координаты валидны — распаковываем кортеж (lat, lon)
            lat, lon = coords
            break     # выходим из цикла
        else:
            print("Повторите ввод координат.\n")

    # SQL-запрос: считаем расстояние от введённой точки до каждого рынка
    # Используем формулу "Haversine" через функцию acos для расчёта расстояния в милях
    # 3959 — радиус Земли в милях
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
    # Параметры передаём 6 раз — т.к. формула дублируется в SELECT и WHERE
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
    # Запрашиваем у пользователя ID и проверяем его на целое число
    market_id = validate_id(input("Введите ID рынка: ").strip())
    if market_id is None:
        return # если ID не число — выходим
    
    # Просим пользователя подтвердить удаление
    confirm = input(f"Удалить рынок {market_id}? (y/n): ").strip().lower()
    if confirm == "y":
        # Удаляем рынок из таблицы markets по ID
        execute_query("DELETE FROM markets WHERE id = %s", (market_id,))
        print("Рынок удалён.")
    else:
        print("Удаление отменено.")

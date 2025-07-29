from .db import execute_query  # импортируем функцию для выполнения SQL-запросов
from .utils import paginate    # импортируем функцию пагинации (переход между страницами)


def show_markets_by_category():
    """
    Показывает рынки по выбранной категории с пагинацией.
    Работает следующим образом:
    - Показывает список всех категорий с их ID.
    - Пользователь выбирает нужную категорию по ID.
    - Выводим все рынки, относящиеся к этой категории, постранично (по 20 штук).
    """
    
    # === Шаг 1. Получаем список всех категорий из таблицы categories ===
    # Результат: список словарей с полями 'id' и 'name'
    categories = execute_query("SELECT id, name FROM categories ORDER BY id", fetch=True)

    if not categories:
        print("Нет категорий в базе данных.") # если таблица пустая — выводим сообщение и выходим
        return

    # === Основной цикл — позволяет выбрать категорию и листать результаты ===
    while True:
        # Выводим все категории на экран
        print("\n=== Список категорий ===")
        for cat in categories:
            print(f"{cat['id']}. {cat['name']}")
        print("0. Выйти в меню")

        # Запрашиваем у пользователя ID категории
        category_id = input("Введите ID категории (или 0 для выхода): ").strip()
        
        if category_id == "0":
            return  # выход в главное меню
        if not category_id.isdigit():
            print("Ошибка: нужно ввести число.")
            continue

        # Проверяем, существует ли введённый ID среди всех категорий
        category_name = None
        for cat in categories:
            if str(cat['id']) == category_id:
                category_name = cat['name'] # сохраняем название категории
                break

        if not category_name:
            print("Такой категории нет. Повторите ввод.")
            continue

        # === Шаг 2. Пагинация результатов ===
        per_page = 20  # количество рынков на одной странице
        offset = 0     # сдвиг по записям
        
        # Считаем общее количество рынков по выбранной категории — для расчёта страниц
        count_query = """
            SELECT COUNT(*) FROM markets m
            JOIN market_categories mc ON mc.market_id = m.id
            WHERE mc.category_id = %s
        """
        total = execute_query(count_query, (category_id,), fetch=True)[0]['count']

        # Вложенный цикл — постраничный просмотр результатов
        while True:
            # SQL-запрос: берём рынки этой категории, вместе с городом и штатом
            query = """
                SELECT m.id, m.name, l.city, l.state
                FROM markets m
                JOIN locations l ON m.location_id = l.id
                JOIN market_categories mc ON mc.market_id = m.id
                WHERE mc.category_id = %s
                ORDER BY m.id
                LIMIT %s OFFSET %s
            """
            # Подставляем параметры: ID категории, лимит записей, сдвиг
            results = execute_query(query, (category_id, per_page, offset), fetch=True)

            if not results:
                if offset == 0:
                    print("Нет рынков для этой категории.")
                else:
                    print("Больше данных нет.")
                offset = 0  # сбрасываем в начало
                break  # выходим на уровень выше (выбор категории)



            # Заголовок страницы
            print(f"\n=== Рынки (категория: {category_name}) с {offset + 1} по {offset + len(results)} ===")
            for r in results:
                print(f"{r['id']}. {r['name']} ({r['city']}, {r['state']})")

            # Переход между страницами (спросим у пользователя)
            offset = paginate(offset, per_page, total)
            if offset is None:
                break  # выход из показа списка рынков (но не из выбора категории)



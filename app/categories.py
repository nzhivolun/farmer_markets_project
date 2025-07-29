from .db import execute_query  # импортируем функцию для работы с БД

def show_markets_by_category():
    """
    Показывает рынки по выбранной категории с пагинацией (сортировка категорий по ID).
    """
    # 1. Получаем список категорий из базы (сортировка по ID)
    categories = execute_query("SELECT id, name FROM categories ORDER BY id", fetch=True)

    if not categories:
        print("Нет категорий в базе данных.")
        return

    while True:
        # Выводим все категории
        print("\n=== Список категорий ===")
        for cat in categories:
            print(f"{cat['id']}. {cat['name']}")
        print("0. Выйти в меню")

        # 2. Выбор категории
        category_id = input("Введите ID категории (или 0 для выхода): ").strip()
        if category_id == "0":
            return  # выход в главное меню
        if not category_id.isdigit():
            print("Ошибка: нужно ввести число.")
            continue

        # Проверка существования категории
        category_name = None
        for cat in categories:
            if str(cat['id']) == category_id:
                category_name = cat['name']
                break

        if not category_name:
            print("Такой категории нет. Повторите ввод.")
            continue

        # === Пагинация ===
        per_page = 20  # количество рынков на странице
        offset = 0

        while True:
            query = """
                SELECT m.id, m.name, l.city, l.state
                FROM markets m
                JOIN locations l ON m.location_id = l.id
                JOIN market_categories mc ON mc.market_id = m.id
                WHERE mc.category_id = %s
                ORDER BY m.id
                LIMIT %s OFFSET %s
            """
            results = execute_query(query, (category_id, per_page, offset), fetch=True)

            if not results:
                if offset == 0:
                    print("Нет рынков для этой категории.")
                else:
                    print("Больше данных нет.")
                command = input("[-] Назад | [0] В меню категорий: ").strip().lower()
                if command == "-":
                    offset -= per_page
                    if offset < 0:
                        offset = 0
                elif command == "0":
                    break
                continue

            # Заголовок страницы
            print(f"\n=== Рынки (категория: {category_name}) с {offset + 1} по {offset + len(results)} ===")
            for r in results:
                print(f"{r['id']}. {r['name']} ({r['city']}, {r['state']})")

            print("======================")
            print("[+] Следующая | [-] Предыдущая | [0] В меню категорий")

            command = input("Ваш выбор: ").strip().lower()
            if command == "+":
                offset += per_page
            elif command == "-":
                offset -= per_page
                if offset < 0:
                    offset = 0
            elif command == "0":
                break
            else:
                print("Неверная команда.")


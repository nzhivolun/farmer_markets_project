# utils.py
# ===========================================================
# Общие функции для проверки данных и навигации
# ===========================================================

def validate_id(input_value):
    """
    Проверяет, что введённое значение — целое число.
    Возвращает int или None.
    """
    if input_value.isdigit():
        return int(input_value)
    else:
        print("Ошибка: ID должно быть числом.")
        return None


def validate_coordinates(lat, lon):
    """
    Проверяет координаты (широта и долгота).
    Возвращает (lat, lon) как float или None, если ошибка.
    """
    try:
        lat = float(lat) # Преобразуем широту в число (например, "59.93" → 59.93 - Санкт-Петербург)
        lon = float(lon) # Преобразуем долготу в число (например, "30.31" → 30.31 - Санкт-Петербург)
    except ValueError:
        print("Ошибка: координаты должны быть числами.")
        return None

    if not (-90 <= lat <= 90 and -180 <= lon <= 180): #  (lat) — это как "верх/низ" на глобусе,  (lon) — это как "лево/право" на глобусе:
        print("Ошибка: широта [-90,90], долгота [-180,180].")
        return None

    return lat, lon


    """
    функция paginate()
    Эта функция помогает организовать постраничный вывод информации, как в социальных сетях или поисковиках, где данные показываются частями (например, по 10 записей на странице).
    Если results пуст (if not results), значит, данных больше нет
    """

def paginate(results, offset, per_page):
    """
    Проверяет, есть ли данные для отображения.
    Возвращает новый offset или None, если нужно выйти.
    """
    if not results:
        print("\nБольше данных нет.")
        if offset > 0:
            offset -= per_page
        command = input("[-] Назад | [0] В меню: ").strip().lower()
        if command == "-":
            offset -= per_page
            if offset < 0:
                offset = 0
            return offset
        elif command == "0":
            return None
    return offset

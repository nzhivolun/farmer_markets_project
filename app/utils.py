# utils.py
# ===========================================================
# Общие функции для проверки данных и навигации
# ===========================================================
import math  # для округления вверх

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

def paginate(offset, per_page, total=None):
    """
    Расширенная пагинация:
    - [+] следующая
    - [-] предыдущая
    - [<<] первая
    - [>>] последняя
    - [0] выход в меню
    - [число] перейти на указанную страницу
    """
    # === Вычисляем текущую и общее количество страниц ===
    if total is not None:
        total_pages = math.ceil(total / per_page)
        current_page = offset // per_page + 1
        print(f"\nСтраница {current_page} из {total_pages}")
    else:
        print("\nПереход между страницами:")

    print("[<<] Первая | [+] Следующая | [-] Предыдущая | [>>] Последняя | [число] Перейти | [0] Меню")

    command = input("Ваш выбор: ").strip().lower()

    if command == "+":
        return offset + per_page
    elif command == "-":
        return max(0, offset - per_page)
    elif command == "<<":
        return 0
    elif command == ">>" and total is not None:
        return (total_pages - 1) * per_page
    elif command == "0":
        return None
    elif command.isdigit():
        page = int(command)
        if total is not None and 1 <= page <= total_pages:
            return (page - 1) * per_page
        else:
            print("Ошибка: номер страницы вне допустимого диапазона.")
            return offset
    else:
        print("Неверная команда.")
        return offset

# main.py
# ===========================================================
# Главный файл приложения фермерских рынков
# Содержит только меню и вызовы функций из модулей
# ===========================================================

from .markets import show_markets, search_market, show_market_details, sort_markets, search_by_radius, delete_market
# from .reviews import add_review, delete_review
from .categories import show_markets_by_category
from .reviews_oop import ReviewManager


def main():
    
    manager = ReviewManager()
    
    """Главное меню приложения"""
    while True:
        print("\n=== МЕНЮ ===")
        print("1. Список рынков")
        print("2. Поиск по городу/штату/индексу")
        print("3. Детали рынка")
        print("4. Добавить отзыв")
        print("5. Удалить отзыв")
        print("6. Сортировка рынков")
        print("7. Поиск по радиусу (30 миль)")
        print("8. Удалить рынок")
        print("9. Показать рынки по категории")
        print("111. Проверка работы класса ReviewManager")
        print("0. Выход")

        choice = input("Выберите пункт: ").strip()

        if choice == "1":
            show_markets()
        elif choice == "2":
            search_market()
        elif choice == "3":
            show_market_details()
        elif choice == "4":
            manager.add_review()
        elif choice == "5":
            manager.delete_review()
        elif choice == "6":
            sort_markets()
        elif choice == "7":
            search_by_radius()
        elif choice == "8":
            delete_market()
        elif choice == "9":
            show_markets_by_category()
            
        elif choice == "111":
            print(f"Состояние: {manager.last_message}")

        elif choice == "0":
            print("Выход...")
            break
        else:
            print("Неверный выбор. Повторите ввод.")


if __name__ == "__main__":
    main()

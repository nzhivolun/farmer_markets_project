# app/reviews_oop.py
# ===========================================================
# НОВЫЙ простой класс для работы с отзывами в стиле ООП.
# - Класс ReviewManager инкапсулирует операции "добавить отзыв" и "удалить отзыв".
# - Внутри использует уже готовую функцию execute_query из db.py (как и в процедурной версии).
# - Для наглядности класс хранит "last_message" — последнее текстовое сообщение об операции.
# ===========================================================

from .db import execute_query  # берём готовую функцию работы с БД (подключение, курсор и т.п.)
from prompt_toolkit import prompt 

class ReviewManager:
    """
    - у нас есть ОБЪЕКТ (review_manager),
    - у объекта есть МЕТОДЫ (add_review, delete_review),
    - у объекта может быть СОСТОЯНИЕ (last_message).
    """

    def __init__(self):
        # last_message будет хранить текст о результатах последней операции.
        # Это просто для наглядности, чтобы увидеть "состояние" объекта.
        self.last_message = "Проверка ООП, созданный класс готов к работе с отзывами."

    def add_review(self):
    # Добавляет отзыв для выбранного рынка

        # Получаем ID рынка (должен быть числом)
        while True:
            market_id = prompt("Введите ID рынка: ").strip()
            if market_id.isdigit():
                market_id = int(market_id)
                break
            print("Ошибка: ID должен быть числом.")

        # Получаем имя и фамилию без доп. проверки
        first_name = prompt("Введите имя: ").strip()
        last_name = prompt("Введите фамилию: ").strip()
        user_name = f"{first_name} {last_name}"

        # Получаем оценку от 1 до 5
        while True:
            rating = prompt("Оценка (1-5): ").strip()
            if rating.isdigit() and 1 <= int(rating) <= 5:
                rating = int(rating)
                break
            print("Ошибка: введите число от 1 до 5.")

        # Получаем текст отзыва (оставляем как есть, без фильтрации)
        review_text = prompt("Текст отзыва: ").strip()

        # Сохраняем отзыв в базу данных
        execute_query(
            "INSERT INTO reviews (market_id, user_name, rating, review_text) VALUES (%s, %s, %s, %s)",
            (market_id, user_name, rating, review_text)
        )
        print("Отзыв добавлен.")

    # ===========================================================
    # === 2. Удаление отзыва по ID ===
    # ===========================================================
    def delete_review(self):
        # Удаляет отзыв по ID
        while True:
            review_id = prompt("Введите ID отзыва: ").strip()
            if review_id.isdigit():
                break
            print("Ошибка: ID должен быть числом.")
            
        execute_query("DELETE FROM reviews WHERE id = %s", (review_id,))
        print("Отзыв удалён.")
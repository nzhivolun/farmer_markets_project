# web/markets/models.py

# ===============================================
# Описание моделей под уже существующие таблицы.
# ВАЖНО: managed = False — значит Django НЕ будет
# создавать/изменять эти таблицы миграциями.
# Мы лишь даём Django "карту" полей для удобных запросов.
# ===============================================

from django.db import models

class Location(models.Model):
    # Таблица: locations
    # Поля названы максимально просто и понятно.
    street = models.CharField("Улица", max_length=255, null=True, blank=True)
    city = models.CharField("Город", max_length=100)
    county = models.CharField("Округ", max_length=100, null=True, blank=True)
    state = models.CharField("Штат", max_length=50)
    zip = models.CharField("Почтовый индекс", max_length=20, null=True, blank=True)

    class Meta:
        managed = False              # Django НЕ управляет этой таблицей
        db_table = "locations"       # точное имя таблицы в БД
        verbose_name = "Локация"
        verbose_name_plural = "Локации"

    def __str__(self):
        # Строковое представление объекта (для админки и отладки)
        # Пишем так, чтобы было понятно, что это за локация
        return f"{self.city}, {self.state} {self.zip or ''}".strip()


class Market(models.Model):
    # Таблица: markets
    # Связываем рынок с локацией через внешний ключ на поле location_id.
    name = models.CharField("Название", max_length=255)
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        db_column="location_id",         # указываем точное имя столбца внешнего ключа
        related_name="markets",          # удобное имя обратной связи: location.markets.all()
    )
    website = models.CharField("Сайт", max_length=255, null=True, blank=True)
    facebook = models.CharField("Facebook", max_length=255, null=True, blank=True)
    twitter = models.CharField("Twitter", max_length=255, null=True, blank=True)
    youtube = models.CharField("YouTube", max_length=255, null=True, blank=True)
    other_media = models.TextField("Другое", null=True, blank=True)
    latitude = models.DecimalField("Широта", max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField("Долгота", max_digits=10, decimal_places=6, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "markets"
        verbose_name = "Рынок"
        verbose_name_plural = "Рынки"
        permissions = [
            ("can_delete_market", "Может удалять рынки"),
            ("can_create_market", "Может создавать рынки"),
        ]

    def __str__(self):
        return f"[{self.pk}] {self.name}"


from django.contrib.auth.models import User  # добавляем импорт

class Review(models.Model):
    # Таблица: reviews
    market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
        db_column="market_id",
        related_name="reviews"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="user_reviews",
        null=True,
        blank=True,
        verbose_name="Автор отзыва"
    )
    user_name = models.CharField("Пользователь", max_length=100)
    rating = models.IntegerField("Оценка")                      
    review_text = models.TextField("Текст отзыва", null=True, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=False, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "reviews"
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        permissions = [
            ("can_moderate_reviews", "Может удалять все отзывы (модерация)"),
        ]

    def __str__(self):
        return f"#{self.pk} {self.user_name} → {self.rating}"



class Category(models.Model):
    # Таблица: categories
    # Словарь категорий.
    name = models.CharField("Название категории", max_length=100, unique=True)

    class Meta:
        managed = False
        db_table = "categories"
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

# Примечание по связям рынок—категория:
# Скорее всего, связь хранится в таблице market_categories (составной ключ market_id+category_id).
# Django не любит составные PK, поэтому простую ORM-модель делать не будем.
# Когда понадобятся категории рынка или рынки по категории — воспользуемся простым SQL в view.

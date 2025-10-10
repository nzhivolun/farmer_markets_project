# web/markets/admin.py

# ======================================================
# Регистрируем модели в админке, чтобы быстро смотреть данные.
# Так как managed=False, мы осторожно относимся к правкам из админки.
# Для начала оставим дефолтную регистрацию — можно будет править/ограничить позже.
# ======================================================

from django.contrib import admin
from .models import Location, Market, Review, Category

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("id", "city", "state", "zip", "street")
    search_fields = ("city", "state", "zip", "street")

@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "location", "website")
    search_fields = ("name",)
    list_select_related = ("location",)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "market", "user_name", "rating", "created_at")
    search_fields = ("user_name", "review_text")
    list_filter = ("rating",)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)

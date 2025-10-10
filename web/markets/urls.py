# web/markets/urls.py
# =========================
# Здесь регистрируем маршруты (адреса) для приложения markets.
# Мы хотим, чтобы главная "/" открывала нашу страницу "dashboard".

from django.urls import path
from . import views

app_name = "markets"  # пространство имён для {% url 'markets:dashboard' %}

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path("list/", views.markets_list, name="list"),
    path("markets_search/", views.markets_search, name="markets_search"),
    path("details/", views.market_details, name="details"),
    path("reviews/", views.reviews_page, name="reviews"),
    path("sort/", views.sort_markets, name="sort_markets"),
    path("radius/", views.search_by_radius, name="search_by_radius"),
    path("delete_market/", views.delete_market, name="delete_market"),
    path("by_category/", views.markets_by_category, name="by_category"),
    path("register/", views.register, name="register"),
    path("delete_review/", views.delete_review, name="delete_review"),
]

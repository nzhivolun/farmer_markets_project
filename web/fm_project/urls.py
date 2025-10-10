# web/fm_project/urls.py
# ======================
# Подключаем urls нашего приложения "markets" к корню сайта.

from django.contrib import admin
from django.urls import path, include
# Отдача статики в режиме разработки (DEBUG=True)
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.conf.urls.i18n import i18n_patterns


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("markets.urls")),
    path('i18n/', include('django.conf.urls.i18n')),  # ← обязательно
]

# В DEV добавляем маршруты для STATIC_URL
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
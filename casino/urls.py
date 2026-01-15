from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("casino.roulette.urls")),
    path('coinflip/', include("casino.coinflip.urls")),
    path('login/', include("casino.login.urls")),
    path('', include("casino.user_mgr.urls")),
    path('slots/', include("casino.slots.urls")),
    path('api/', include("casino.api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

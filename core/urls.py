from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('inventory/', include('inventory.urls')),
    path('watches/', include('watches.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

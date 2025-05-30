from django.contrib import admin
from django.urls import path, include
from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('partner/', include('apps.partner.urls', namespace='partner')),
    path('api/', include('api.urls')),
    path('', include(apps.get_app_config('oscar').urls[0])),
    path('', include(apps.get_app_config('customer').urls[0])),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
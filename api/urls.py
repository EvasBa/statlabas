from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views # Importuojame vaizdus

# Sukuriame routerį
router = DefaultRouter()
# Registruojame VendorProductViewSet su 'vendor/products' maršrutu
router.register(r'vendor/products', views.VendorProductViewSet, basename='vendor-product')
# Čia vėliau registruosime viešą produktų viewset'ą:
# router.register(r'products', views.PublicProductViewSet, basename='public-product')

# API URL Patternai
urlpatterns = [
    path('', include(router.urls)),
    # Čia galima pridėti kitus API endpoint'us (pvz., autentifikacijai)
    # path('auth/', include('djoser.urls')), # Jei naudotumėte djoser
    # path('auth/', include('djoser.urls.jwt')),
]
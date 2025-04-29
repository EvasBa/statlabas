from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views # Importuojame vaizdus
from .views import CustomTokenObtainPairView, PublicProductViewSet # Importuojame mūsų CustomTokenObtainPairView

# Sukuriame routerį
router = DefaultRouter()
# Registruojame VendorProductViewSet su 'vendor/products' maršrutu
router.register(r'partner/products', views.PartnerProductViewSet, basename='partner-product')
router.register(r'products', views.PublicProductViewSet, basename='product')


# API URL Patternai
urlpatterns = [
    path('', include(router.urls)),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
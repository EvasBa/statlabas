from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('application/', views.VendorApplicationView.as_view(), name='apply'),
    path('dashboard/', views.VendorDashboardView.as_view(), name='dashboard'),
    path('profile/update/', views.VendorProfileUpdateView.as_view(), name='profile_update'),
    path('application/success/', views.VendorApplicationSuccessView.as_view(), name='application-success'),
]
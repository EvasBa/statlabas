from django.urls import path
from . import views

app_name = 'partner'

urlpatterns = [
    path('apply/', views.PartnerApplicationView.as_view(), name='apply'),
    path('dashboard/', views.PartnerDashboardView.as_view(), name='dashboard'),
    path('update/', views.PartnerUpdateView.as_view(), name='update'),
    path('application_success/', views.PartnerApplicationSuccessView.as_view(), name='application_success'),
]
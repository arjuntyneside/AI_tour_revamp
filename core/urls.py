from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import departures

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tours/', views.tours, name='tours'),
    path('customers/', views.customers, name='customers'),
    path('settings/', views.settings, name='settings'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', views.logout, name='logout'),
    path('departures/', departures, name='departures'),
]
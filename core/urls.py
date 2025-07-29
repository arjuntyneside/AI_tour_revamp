from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import departures, customer_detail, tour_detail

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tours/', views.tours, name='tours'),
    path('tours/<int:tour_id>/', tour_detail, name='tour_detail'),
    path('departures/', departures, name='departures'),
    path('customers/', views.customers, name='customers'),
    path('customers/<int:customer_id>/', customer_detail, name='customer_detail'),
    path('settings/', views.settings, name='settings'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', views.logout, name='logout'),
]
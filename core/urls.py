from django.urls import path
from . import views

urlpatterns = [
    # Main navigation - redirect root to departures
    path('', views.departures, name='dashboard'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    
    # AI Document Processing
    path('documents/upload/', views.document_upload, name='document_upload'),
    path('documents/processing/', views.document_processing, name='document_processing'),
    path('documents/<uuid:document_id>/results/', views.document_results, name='document_results'),
    path('documents/<uuid:document_id>/create-tour/', views.create_tour_from_document, name='create_tour_from_document'),
    path('documents/<uuid:document_id>/retry/', views.retry_document_processing, name='retry_document_processing'),
    path('documents/<uuid:document_id>/process/', views.process_document, name='process_document'),
    path('documents/<uuid:document_id>/delete/', views.delete_document, name='delete_document'),
    path('documents/<uuid:document_id>/stop/', views.stop_processing, name='stop_processing'),
    path('documents/<uuid:document_id>/status/', views.processing_status, name='processing_status'),
    
    # Tour Management
    path('tours/', views.tours, name='tours'),
    path('tours/<uuid:tour_id>/', views.tour_detail, name='tour_detail'),
    path('departures/', views.departures, name='departures'),
    path('departures/create/', views.create_departure, name='create_departure'),
    path('departures/<uuid:departure_id>/', views.departure_detail, name='departure_detail'),
    path('departures/<uuid:departure_id>/edit/', views.edit_departure, name='edit_departure'),
    path('departures/<uuid:departure_id>/delete/', views.delete_departure, name='delete_departure'),
    
    # Customer Management
    path('customers/', views.customers, name='customers'),
    path('customers/<uuid:customer_id>/', views.customer_detail, name='customer_detail'),
    
    # Booking Management
    path('bookings/', views.bookings, name='bookings'),
    
    # Analytics and AI Insights
    path('analytics/', views.analytics, name='analytics'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    
    # Settings
    path('settings/', views.settings, name='settings'),
    
    # AI Processing Webhook
    path('api/ai-webhook/', views.ai_processing_webhook, name='ai_processing_webhook'),
]
from django.contrib import admin
from .models import (
    TourOperator, TourOperatorUser, DocumentUpload, AIProcessingJob,
    Tour, TourDeparture, Customer, Booking, CustomerNote, AIAnalytics
)

@admin.register(TourOperator)
class TourOperatorAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'name', 'email', 'subscription_plan', 'subscription_status', 'created_date']
    list_filter = ['subscription_plan', 'subscription_status', 'created_date']
    search_fields = ['company_name', 'name', 'email']
    readonly_fields = ['id', 'created_date', 'updated_date']

@admin.register(TourOperatorUser)
class TourOperatorUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'tour_operator', 'role', 'is_active', 'created_date']
    list_filter = ['role', 'is_active', 'created_date']
    search_fields = ['user__username', 'user__email', 'tour_operator__company_name']

@admin.register(DocumentUpload)
class DocumentUploadAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'tour_operator', 'processing_status', 'uploaded_date', 'confidence_score']
    list_filter = ['processing_status', 'file_type', 'uploaded_date']
    search_fields = ['file_name', 'tour_operator__company_name']
    readonly_fields = ['id', 'uploaded_date', 'processed_date']

@admin.register(AIProcessingJob)
class AIProcessingJobAdmin(admin.ModelAdmin):
    list_display = ['job_type', 'document', 'status', 'created_date', 'completed_date']
    list_filter = ['job_type', 'status', 'created_date']
    search_fields = ['document__file_name', 'document__tour_operator__company_name']
    readonly_fields = ['id', 'created_date', 'completed_date']

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ['title', 'tour_operator', 'destination', 'duration_days', 'status', 'ai_extraction_confidence']
    list_filter = ['status', 'difficulty_level', 'seasonal_demand', 'created_date']
    search_fields = ['title', 'destination', 'tour_operator__company_name']
    readonly_fields = ['id', 'created_date', 'updated_date', 'ai_processed_date']

@admin.register(TourDeparture)
class TourDepartureAdmin(admin.ModelAdmin):
    list_display = ['tour', 'departure_date', 'status', 'total_bookings', 'available_spots', 'ai_demand_score']
    list_filter = ['status', 'departure_date', 'created_date']
    search_fields = ['tour__title', 'tour__tour_operator__company_name']
    readonly_fields = ['id', 'created_date']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'tour_operator', 'ai_customer_segment', 'total_spent', 'bookings_count', 'ai_churn_probability']
    list_filter = ['ai_customer_segment', 'created_date']
    search_fields = ['full_name', 'email', 'tour_operator__company_name']
    readonly_fields = ['id', 'created_date', 'updated_date']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['customer', 'tour', 'departure', 'number_of_people', 'total_amount', 'status', 'ai_cancellation_risk']
    list_filter = ['status', 'booking_date']
    search_fields = ['customer__full_name', 'tour__title', 'tour__tour_operator__company_name']
    readonly_fields = ['id', 'booking_date']

@admin.register(CustomerNote)
class CustomerNoteAdmin(admin.ModelAdmin):
    list_display = ['customer', 'created_by', 'ai_sentiment', 'created_date']
    list_filter = ['ai_sentiment', 'created_date']
    search_fields = ['customer__full_name', 'note_text']
    readonly_fields = ['created_date']

@admin.register(AIAnalytics)
class AIAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['tour_operator', 'analytics_type', 'generated_date', 'confidence_score']
    list_filter = ['analytics_type', 'generated_date']
    search_fields = ['tour_operator__company_name']
    readonly_fields = ['id', 'generated_date']

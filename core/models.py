from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

# Create your models here.

class TourOperator(models.Model):
    """Multi-tenant model for tour operators"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Subscription and billing
    subscription_plan = models.CharField(max_length=50, default='basic', choices=[
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ])
    subscription_status = models.CharField(max_length=20, default='active', choices=[
        ('active', 'Active'),
        ('trial', 'Trial'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    ])
    subscription_end_date = models.DateField(null=True, blank=True)
    
    # AI features enabled
    ai_document_processing = models.BooleanField(default=True)
    ai_pricing_analysis = models.BooleanField(default=True)
    ai_demand_forecasting = models.BooleanField(default=True)
    ai_customer_segmentation = models.BooleanField(default=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.company_name} ({self.name})"
    
    @property
    def is_subscription_active(self):
        """Check if subscription is active"""
        if self.subscription_status in ['active', 'trial']:
            return True
        return False

class TourOperatorUser(models.Model):
    """Users associated with tour operators"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tour_operator = models.ForeignKey(TourOperator, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=50, default='staff', choices=[
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
        ('viewer', 'Viewer'),
    ])
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.tour_operator.company_name}"

class DocumentUpload(models.Model):
    """Model for uploaded documents (brochures, PDFs, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tour_operator = models.ForeignKey(TourOperator, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # File information
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=50, help_text="PDF, DOCX, etc.")
    file_path = models.CharField(max_length=500)
    
    # Processing status
    processing_status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reviewed', 'Reviewed'),
    ])
    
    # AI extraction results
    extracted_data = models.JSONField(default=dict, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    processing_errors = models.TextField(blank=True, null=True)
    processing_notes = models.TextField(blank=True, null=True, help_text="Additional notes about processing")
    
    # Timestamps
    uploaded_date = models.DateTimeField(auto_now_add=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.file_name} - {self.tour_operator.company_name}"

class AIProcessingJob(models.Model):
    """Track AI processing jobs"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(DocumentUpload, on_delete=models.CASCADE, related_name='ai_jobs')
    job_type = models.CharField(max_length=50, choices=[
        ('document_extraction', 'Document Extraction'),
        ('pricing_analysis', 'Pricing Analysis'),
        ('demand_forecasting', 'Demand Forecasting'),
        ('customer_segmentation', 'Customer Segmentation'),
    ])
    
    status = models.CharField(max_length=20, default='queued', choices=[
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    
    result_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.job_type} - {self.document.file_name}"

class Tour(models.Model):
    """Enhanced Tour model with AI insights"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tour_operator = models.ForeignKey(TourOperator, on_delete=models.CASCADE, related_name='tours')
    source_document = models.ForeignKey(DocumentUpload, on_delete=models.SET_NULL, null=True, blank=True, related_name='extracted_tours')
    
    # Basic tour information
    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    duration_days = models.PositiveIntegerField()
    max_group_size = models.PositiveIntegerField(default=15)
    
    # Pricing
    pricing_type = models.CharField(max_length=20, choices=[
        ('per_person', 'Price Per Person'),
        ('per_group', 'Price Per Group'),
        ('custom', 'Custom Pricing'),
    ], default='per_person')
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_per_group = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # AI-suggested pricing
    ai_suggested_price_per_person = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ai_pricing_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Content
    description = models.TextField(default='')
    highlights = models.TextField(default='')
    included_services = models.TextField(default='')
    excluded_services = models.TextField(blank=True, default='')
    
    # AI-enhanced fields
    difficulty_level = models.CharField(max_length=20, choices=[
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('challenging', 'Challenging'),
        ('expert', 'Expert'),
    ], default='moderate')
    
    seasonal_demand = models.CharField(max_length=20, choices=[
        ('high', 'High Season'),
        ('medium', 'Medium Season'),
        ('low', 'Low Season'),
        ('year_round', 'Year Round'),
    ], default='medium')
    
    # AI demand forecasting
    ai_demand_forecast = models.JSONField(default=dict, blank=True)
    ai_optimal_departure_dates = models.JSONField(default=list, blank=True)
    
    # Financial tracking
    cost_per_person = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    operational_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit_margin_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=20, default='draft', choices=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ])
    
    # AI processing metadata
    ai_extraction_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_processed_date = models.DateTimeField(null=True, blank=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.tour_operator.company_name}"
    
    @property
    def effective_price_per_person(self):
        """Get effective price per person"""
        if self.pricing_type == 'per_person':
            return self.price_per_person
        elif self.pricing_type == 'per_group' and self.max_group_size > 0:
            return self.price_per_group / self.max_group_size
        return 0
    
    @property
    def profit_per_person(self):
        """Calculate profit per person"""
        return self.effective_price_per_person - self.cost_per_person
    
    @property
    def total_profit_potential(self):
        """Calculate total profit potential"""
        return self.profit_per_person * self.max_group_size

class TourDeparture(models.Model):
    """Tour departure dates with AI optimization"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='departures')
    departure_date = models.DateField()
    
    # AI-enhanced fields
    ai_demand_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_optimal_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Booking tracking
    total_bookings = models.PositiveIntegerField(default=0)
    available_spots = models.PositiveIntegerField()
    
    # Status
    status = models.CharField(max_length=20, default='scheduled', choices=[
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ])
    
    created_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.tour.title} - {self.departure_date}"
    
    def save(self, *args, **kwargs):
        if not self.available_spots:
            self.available_spots = self.tour.max_group_size
        super().save(*args, **kwargs)

class Customer(models.Model):
    """Enhanced customer model with AI segmentation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tour_operator = models.ForeignKey(TourOperator, on_delete=models.CASCADE, related_name='customers')
    
    # Basic information
    initials = models.CharField(max_length=10)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    
    # AI-enhanced segmentation
    ai_customer_segment = models.CharField(max_length=20, choices=[
        ('premium', 'Premium'),
        ('regular', 'Regular'),
        ('budget', 'Budget'),
        ('new', 'New Customer'),
        ('loyal', 'Loyal'),
        ('at_risk', 'At Risk'),
    ], default='new')
    
    ai_segmentation_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_next_booking_prediction = models.DateField(null=True, blank=True)
    ai_recommended_tours = models.JSONField(default=list, blank=True)
    
    # Financial tracking
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bookings_count = models.PositiveIntegerField(default=0)
    cancellation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    last_interaction_date = models.DateField(null=True, blank=True)
    
    # Customer lifetime value
    ai_customer_lifetime_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ai_churn_probability = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.tour_operator.company_name}"
    
    @property
    def average_booking_value(self):
        """Calculate average booking value"""
        if self.bookings_count > 0:
            return self.total_spent / self.bookings_count
        return 0

class Booking(models.Model):
    """Booking model with AI insights"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tour_operator = models.ForeignKey(TourOperator, on_delete=models.CASCADE, related_name='bookings')
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='bookings')
    departure = models.ForeignKey(TourDeparture, on_delete=models.CASCADE, related_name='bookings')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='bookings')
    
    # Booking details
    booking_date = models.DateTimeField(auto_now_add=True)
    number_of_people = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, default='confirmed', choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ])
    
    # AI insights
    ai_booking_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_cancellation_risk = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.customer.full_name} - {self.tour.title}"

class CustomerNote(models.Model):
    """Customer notes with AI insights"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='notes')
    note_text = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    
    # AI sentiment analysis
    ai_sentiment = models.CharField(max_length=20, null=True, blank=True, choices=[
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ])
    
    def __str__(self):
        return f"Note for {self.customer.full_name} - {self.created_date.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-created_date']

class AIAnalytics(models.Model):
    """AI-generated analytics and insights"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tour_operator = models.ForeignKey(TourOperator, on_delete=models.CASCADE, related_name='ai_analytics')
    
    # Analytics type
    analytics_type = models.CharField(max_length=50, choices=[
        ('revenue_forecast', 'Revenue Forecast'),
        ('demand_analysis', 'Demand Analysis'),
        ('customer_insights', 'Customer Insights'),
        ('pricing_optimization', 'Pricing Optimization'),
        ('operational_efficiency', 'Operational Efficiency'),
    ])
    
    # Data
    analytics_data = models.JSONField()
    generated_date = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    processing_time = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.analytics_type} - {self.tour_operator.company_name}"
    
    class Meta:
        ordering = ['-generated_date']

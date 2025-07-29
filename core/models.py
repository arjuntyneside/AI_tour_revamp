from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class TourDeparture(models.Model):
    tour = models.ForeignKey('Tour', on_delete=models.CASCADE, related_name='departures')
    departure_date = models.DateField()

    def __str__(self):
        return f"{self.tour.title} on {self.departure_date}"

class Customer(models.Model):
    CUSTOMER_SEGMENT_CHOICES = [
        ('premium', 'Premium'),
        ('regular', 'Regular'),
        ('budget', 'Budget'),
        ('new', 'New Customer'),
    ]
    
    initials = models.CharField(max_length=10)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    bookings_count = models.PositiveIntegerField(default=0)
    last_interaction_date = models.DateField(null=True, blank=True)
    
    # Financial fields
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total amount spent by customer")
    cancellation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Percentage of bookings cancelled")
    customer_segment = models.CharField(max_length=20, choices=CUSTOMER_SEGMENT_CHOICES, default='new', help_text="Customer segment classification")

    def __str__(self):
        return f"{self.initials} - {self.full_name}"
    
    @property
    def average_booking_value(self):
        """Calculate average booking value"""
        if self.bookings_count > 0:
            return self.total_spent / self.bookings_count
        return 0
    
    @property
    def customer_lifetime_value(self):
        """Calculate customer lifetime value"""
        return self.total_spent * (1 - self.cancellation_rate / 100)

class CustomerNote(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='notes')
    note_text = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Note for {self.customer.full_name} - {self.created_date.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-created_date']

def tour_image_path(instance, filename):
    """Generate file path for tour images"""
    return f'tour_images/{instance.id}/{filename}'

class Tour(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('challenging', 'Challenging'),
        ('expert', 'Expert'),
    ]
    
    SEASONAL_DEMAND_CHOICES = [
        ('high', 'High Season'),
        ('medium', 'Medium Season'),
        ('low', 'Low Season'),
        ('year_round', 'Year Round'),
    ]
    
    PRICING_TYPE_CHOICES = [
        ('per_person', 'Price Per Person (PPP)'),
        ('per_group', 'Price Per Group'),
    ]
    
    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    duration_days = models.PositiveIntegerField()
    
    # Pricing fields - clarified
    pricing_type = models.CharField(max_length=20, choices=PRICING_TYPE_CHOICES, default='per_person', help_text="How is this tour priced?")
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Price per person (PPP)")
    price_per_group = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total price for the entire group")
    
    description = models.TextField()
    highlights = models.TextField(help_text="Key highlights of the tour")
    included_services = models.TextField(help_text="What's included in the tour")
    excluded_services = models.TextField(help_text="What's not included in the tour", blank=True)
    max_group_size = models.PositiveIntegerField()
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='moderate')
    image = models.ImageField(upload_to=tour_image_path, blank=True, null=True, help_text="Tour image")
    image_url = models.URLField(blank=True, null=True, help_text="External image URL (alternative to file upload)")
    
    # Financial fields
    cost_per_person = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Cost per person for this tour")
    operational_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Fixed operational costs for this tour")
    profit_margin_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Expected profit margin percentage")
    seasonal_demand = models.CharField(max_length=20, choices=SEASONAL_DEMAND_CHOICES, default='medium', help_text="Seasonal demand pattern")
    
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.destination}"

    class Meta:
        ordering = ['-created_date']
    
    @property
    def effective_price_per_person(self):
        """Get the effective price per person regardless of pricing type"""
        if self.pricing_type == 'per_person':
            return self.price_per_person
        elif self.pricing_type == 'per_group' and self.max_group_size > 0:
            return self.price_per_group / self.max_group_size
        return 0
    
    @property
    def profit_per_person(self):
        """Calculate profit per person"""
        if self.cost_per_person > 0:
            return self.effective_price_per_person - self.cost_per_person
        return 0
    
    @property
    def total_profit_potential(self):
        """Calculate total profit potential for full group"""
        return self.profit_per_person * self.max_group_size
    
    @property
    def actual_profit_margin(self):
        """Calculate actual profit margin percentage"""
        if self.effective_price_per_person > 0:
            return (self.profit_per_person / self.effective_price_per_person) * 100
        return 0

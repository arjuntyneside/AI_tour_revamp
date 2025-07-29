from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Departure(models.Model):
    title = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    duration_days = models.PositiveIntegerField()
    departure_date = models.DateField()
    group_size_current = models.PositiveIntegerField()
    group_size_max = models.PositiveIntegerField()
    price_gbp = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.title} ({self.country}) on {self.departure_date}"

class Customer(models.Model):
    initials = models.CharField(max_length=10)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    bookings_count = models.PositiveIntegerField(default=0)
    last_interaction_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.initials} - {self.full_name}"

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
    
    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    duration_days = models.PositiveIntegerField()
    price_gbp = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    highlights = models.TextField(help_text="Key highlights of the tour")
    included_services = models.TextField(help_text="What's included in the tour")
    excluded_services = models.TextField(help_text="What's not included in the tour", blank=True)
    max_group_size = models.PositiveIntegerField()
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='moderate')
    image = models.ImageField(upload_to=tour_image_path, blank=True, null=True, help_text="Tour image")
    image_url = models.URLField(blank=True, null=True, help_text="External image URL (alternative to file upload)")
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.destination}"

    class Meta:
        ordering = ['-created_date']

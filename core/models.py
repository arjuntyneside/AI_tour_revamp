from django.db import models

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

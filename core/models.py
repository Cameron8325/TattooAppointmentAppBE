from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_artist = models.BooleanField(default=False)
    
class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    artist = models.ForeignKey('User', on_delete=models.CASCADE, related_name='services')

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    client = models.ForeignKey('User', on_delete=models.CASCADE, related_name='appointments')
    artist = models.ForeignKey('User', on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
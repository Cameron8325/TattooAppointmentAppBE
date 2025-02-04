from django.db import models
from django.contrib.auth.models import AbstractUser

# User model for authentication and artist designation
class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Admin"),  # Manager/Superuser
        ("employee", "Employee"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="employee")

# ClientProfile model for storing client-specific details
class ClientProfile(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    artist = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='clients'  # Tracks clients assigned to an artist
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# Service model for the types of services offered by artists
class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    artist = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='services'
    )

    def __str__(self):
        return self.name

# Appointment model for scheduling appointments
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    client = models.ForeignKey(
        'ClientProfile',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    artist = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    service = models.ForeignKey(
        'Service',
        on_delete=models.CASCADE
    )
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    requires_approval = models.BooleanField(default=False)  # ✅ Tracks if approval is needed
    notes = models.TextField(
        null=True,
        blank=True
    )  # For small notes about the tattoo

    def __str__(self):
        return f"Appointment for {self.client} with {self.artist} on {self.date}"

# Notification model for manager approvals
class Notifications(models.Model):
    APPOINTMENT_ACTIONS = [
        ('created', 'Created Appointment'),
        ('updated', 'Updated Appointment'),
        ('canceled', 'Canceled Appointment'),
        ('pending_approval', 'Pending Approval'),
    ]

    employee = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    action = models.CharField(
        max_length=20,
        choices=APPOINTMENT_ACTIONS,
        default='pending_approval'
    )
    appointment = models.ForeignKey(
        'Appointment',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('denied', 'Denied'),
        ],
        default='pending'
    )

    def __str__(self):
        return f"Notification from {self.employee} - {self.action} ({self.status})"

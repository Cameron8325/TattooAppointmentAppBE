from django.db import models
from django.contrib.auth.models import AbstractUser

# User model for authentication and employee designation
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
    employee = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='clients'  # Tracks clients assigned to an employee
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# Service model for the types of services offered by employees
class Service(models.Model):
    SERVICE_CHOICES = [
        ("service_1", "Service 1"),
        ("service_2", "Service 2"),
        ("service_3", "Service 3"),
    ]
    
    name = models.CharField(max_length=100, choices=SERVICE_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.get_name_display()



# Appointment model for scheduling appointments
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    client = models.ForeignKey(
        'ClientProfile',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    employee = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    service = models.ForeignKey(
        'Service',
        on_delete=models.CASCADE
    )
    date = models.DateField()
    time = models.TimeField()           # Start time
    end_time = models.TimeField()       # New field for end time
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='confirmed'
    )
    requires_approval = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.requires_approval and self.status != "pending":
            self.status = "pending"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Appointment for {self.client} with {self.employee} on {self.date}"


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

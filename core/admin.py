from django.contrib import admin
from .models import User, Service, Appointment

admin.site.register(User)
admin.site.register(Service)
admin.site.register(Appointment)

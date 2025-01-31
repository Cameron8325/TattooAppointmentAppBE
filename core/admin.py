from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import Service, Appointment

User = get_user_model()

class CustomUserAdmin(UserAdmin):
    """
    Extends Django's built-in UserAdmin to ensure passwords are properly hashed
    and the 'Change Password' button is available in the admin panel.
    """
    fieldsets = UserAdmin.fieldsets + (
        ("Custom Fields", {"fields": ("role",)}),
    )

# ✅ Register the User model with UserAdmin
admin.site.register(User, CustomUserAdmin)

# Register other models as usual
admin.site.register(Service)
admin.site.register(Appointment)

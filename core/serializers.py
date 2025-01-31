from rest_framework import serializers
from django.contrib.auth.models import User
from .models import User, Service, Appointment, ClientProfile, Notifications

# User Serializer
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model with password hashing.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    def create(self, validated_data):
        """
        Create a new user and hash the password.
        """
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email", ""),
        )
        return user

    def update(self, instance, validated_data):
        """
        Update user password securely.
        """
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)

        if "password" in validated_data:
            instance.set_password(validated_data["password"])

        instance.save()
        return instance

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role"]


# Client Profile Serializer
class ClientProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for ClientProfile model.
    """
    artist = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = ClientProfile
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'artist']

# Service Serializer
class ServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for Service model.
    """
    artist = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price', 'artist']

# Appointment Serializer
class AppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Appointment model.
    """
    client = serializers.PrimaryKeyRelatedField(queryset=ClientProfile.objects.all())
    artist = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())

    class Meta:
        model = Appointment
        fields = ['id', 'client', 'artist', 'service', 'date', 'time', 'status', 'notes']

# Appointment Overview Serializer
class AppointmentOverviewSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    completed = serializers.IntegerField()
    pending = serializers.IntegerField()
    canceled = serializers.IntegerField()

# Notification Serializer
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = ['id', 'employee', 'action', 'timestamp', 'status']

# Authentication Serializer for Login
class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login. Accepts username and password.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

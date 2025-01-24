from rest_framework import serializers
from .models import User, Service, Appointment, ClientProfile, Notifications

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_artist']

class ClientProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for ClientProfile model.
    """
    artist = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = ClientProfile
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'artist']

class ServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for Service model.
    """
    artist = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price', 'artist']

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

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = ['id', 'employee', 'action', 'timestamp', 'status']
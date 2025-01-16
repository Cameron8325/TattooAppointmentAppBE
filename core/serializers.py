from rest_framework import serializers
from .models import User, Service, Appointment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_artist']

class ServiceSerializer(serializers.ModelSerializer):
    artist = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price', 'artist']

class AppointmentSerializer(serializers.ModelSerializer):
    client = serializers.StringRelatedField(read_only=True)
    artist = serializers.StringRelatedField(read_only=True)
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'client', 'artist', 'service', 'date', 'time', 'status']
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

    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):  # ✅ Must match the field name
        return f"{obj.first_name} {obj.last_name}".strip()

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "email", "password", "role"]


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
    name_display = serializers.CharField(source='get_name_display', read_only=True)  # ✅ Fix applied

    class Meta:
        model = Service
        fields = ['id', 'name', 'name_display', 'description', 'price']

    class Meta:
        model = Service
        fields = ['id', 'name', 'name_display', 'description', 'price']


# Appointment Serializer
class AppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Appointment model.
    """
    client = ClientProfileSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=ClientProfile.objects.all(), source="client", write_only=True, required=False
    )
    new_client = ClientProfileSerializer(write_only=True, required=False)  # ✅ Allow new client data

    artist = UserSerializer(read_only=True)
    artist_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="artist", write_only=True
    )
    status = serializers.CharField(source='get_status_display', read_only=True)

    service = serializers.StringRelatedField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)  # ✅ Required field remains unchanged

    requires_approval = serializers.BooleanField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id", "client", "client_id", "new_client", "artist", "artist_id", "service", "date", "time",
            "price", "status", "notes", "requires_approval"
        ]

    def validate(self, data):
        """
        Ensure that only one of `client_id` or `new_client` is provided.
        """
        if data.get("client_id") and data.get("new_client"):
            raise serializers.ValidationError("Provide either 'client_id' or 'new_client', not both.")
        return data

    def validate_price(self, value):
        """
        Ensure price is always provided and is a positive number.
        """
        if value is None:
            raise serializers.ValidationError("Price is required.")
        if value < 0:
            raise serializers.ValidationError("Price must be a positive number.")
        return value

    def create(self, validated_data):
        """
        Handle creating an appointment with a new client if necessary.
        """
        new_client_data = validated_data.pop("new_client", None)  # Extract new client data if provided
        client = validated_data.pop("client", None)  # Extract existing client if provided

        if new_client_data:
            client = ClientProfile.objects.create(**new_client_data)  # ✅ Creates a new client

        return Appointment.objects.create(client=client, **validated_data)


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

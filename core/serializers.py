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
    employee = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = ClientProfile
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'employee']

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
    client = ClientProfileSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=ClientProfile.objects.all(), source="client", write_only=True, required=False
    )
    new_client = ClientProfileSerializer(write_only=True, required=False)

    employee = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=True
    )
    service = serializers.SlugRelatedField(slug_field="name", queryset=Service.objects.all())
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    end_time = serializers.TimeField()  # Add end_time here

    class Meta:
        model = Appointment
        fields = [
            "id", "client", "client_id", "new_client", "employee", "service",
            "date", "time", "end_time", "price", "status", "notes", "requires_approval"
        ]

    def validate(self, data):
        client = data.get("client") if "client" in data else getattr(self.instance, "client", None)
        new_client = data.get("new_client") if "new_client" in data else None

        if client and new_client:
            raise serializers.ValidationError({"error": "Provide either 'client_id' or 'new_client', not both."})
        if not client and not new_client:
            raise serializers.ValidationError({"client": "A client is required."})
        
        # Validate that end_time is later than start time
        start_time = data.get("time")
        end_time = data.get("end_time")
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})
        return data

    def create(self, validated_data):
        client = validated_data.pop("client", None)
        new_client_data = validated_data.pop("new_client", None)

        if client is None and new_client_data:
            email = new_client_data.get("email")
            client = ClientProfile.objects.filter(email=email).first()
            if client is None:
                client = ClientProfile.objects.create(**new_client_data)
        if client is None:
            raise serializers.ValidationError({"client": "A client is required."})
        return Appointment.objects.create(client=client, **validated_data)

    def update(self, instance, validated_data):
        validated_data["client"] = validated_data.get("client", instance.client)
        return super().update(instance, validated_data)

# Appointment Overview Serializer
class AppointmentOverviewSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    completed = serializers.IntegerField()
    pending = serializers.IntegerField()
    canceled = serializers.IntegerField()

# Notification Serializer
class NotificationSerializer(serializers.ModelSerializer):
    appointment_details = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = Notifications
        fields = [
            "id",
            "employee",
            "employee_name",
            "action",
            "timestamp",
            "status",
            "changes",
            "previous_details",
            "appointment_details",
        ]

    def get_appointment_details(self, obj):
        """
        Return a dictionary of relevant appointment details.
        """
        if obj.appointment:
            return {
                "client": obj.appointment.client.first_name + " " + obj.appointment.client.last_name,
                "artist": obj.appointment.employee.first_name + " " + obj.appointment.employee.last_name,
                "service": obj.appointment.service.name,
                "price": str(obj.appointment.price),
                "date": str(obj.appointment.date),
                "time": str(obj.appointment.time),
                "end_time": str(obj.appointment.end_time),
                "notes": obj.appointment.notes,
            }
        return None

    def get_employee_name(self, obj):
        """
        Get full name of the employee who requested the change.
        """
        return obj.employee.first_name + " " + obj.employee.last_name if obj.employee else "Unknown"


# Authentication Serializer for Login
class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login. Accepts username and password.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

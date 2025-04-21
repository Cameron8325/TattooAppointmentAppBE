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
    employee_name = serializers.SerializerMethodField()  # ✅ Correctly defined
    service = serializers.SlugRelatedField(slug_field="name", queryset=Service.objects.all())
    service_display = serializers.SerializerMethodField()  # ✅ Fixed to use SerializerMethodField
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    end_time = serializers.TimeField()

    class Meta:
        model = Appointment
        fields = [
            "id", "client", "client_id", "new_client", "employee", "employee_name", "service", "service_display",
            "date", "time", "end_time", "price", "status", "notes", "requires_approval"
        ]

    def get_employee_name(self, obj):
        """Return full name of the assigned employee."""
        return f"{obj.employee.first_name} {obj.employee.last_name}".strip() if obj.employee else "N/A"

    def get_service_display(self, obj):
        """Retrieve human-readable service name from choices."""
        return obj.service.get_name_display() if obj.service else "N/A"

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
    no_show = serializers.IntegerField()

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
        if not obj.appointment:
            return None

        # Format time fields into 12‑hour with no leading zero
        raw_t1 = obj.appointment.time.strftime("%I:%M %p")
        t1 = raw_t1.lstrip("0")
        raw_t2 = obj.appointment.end_time.strftime("%I:%M %p")
        t2 = raw_t2.lstrip("0")

        return {
            "client": f"{obj.appointment.client.first_name} {obj.appointment.client.last_name}",
            "artist": f"{obj.appointment.employee.first_name} {obj.appointment.employee.last_name}",
            "service": obj.appointment.service.get_name_display(),
            "price": str(obj.appointment.price),
            "date": obj.appointment.date.strftime("%Y-%m-%d"),
            "time": t1,
            "end_time": t2,
            "notes": obj.appointment.notes or "",
        }

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}" if obj.employee else "Unknown"



# Authentication Serializer for Login
class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login. Accepts username and password.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

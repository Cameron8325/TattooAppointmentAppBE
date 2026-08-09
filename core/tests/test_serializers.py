from datetime import date, time

from django.test import TestCase

from core.models import Appointment, ClientProfile, Notifications, Service, User
from core.serializers import (
    AppointmentSerializer,
    ClientProfileSerializer,
    NotificationSerializer,
    ServiceSerializer,
    UserSerializer,
)


class SerializerTestBase(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="artistuser",
            password="testpass123",
            role="employee",
            first_name="Ari",
            last_name="Stone",
        )
        self.client_profile = ClientProfile.objects.create(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="1234567890",
            employee=self.employee,
        )
        self.service = Service.objects.create(
            name="service_1",
            description="A custom tattoo design.",
            price="150.00",
        )

    def appointment_payload(self, **overrides):
        payload = {
            "client_id": self.client_profile.id,
            "employee": self.employee.id,
            "service": self.service.name,
            "date": "2026-08-25",
            "time": "14:00:00",
            "end_time": "15:00:00",
            "price": "150.00",
            "status": "pending",
        }
        payload.update(overrides)
        return payload


class UserSerializerTest(SerializerTestBase):
    def test_user_serialization(self):
        data = UserSerializer(self.employee).data
        self.assertEqual(data["username"], "artistuser")
        self.assertEqual(data["full_name"], "Ari Stone")
        self.assertEqual(data["role"], "employee")
        self.assertNotIn("password", data)


class ClientProfileSerializerTest(SerializerTestBase):
    def test_client_profile_round_trip(self):
        data = ClientProfileSerializer(self.client_profile).data
        self.assertEqual(data["employee"], self.employee.id)
        self.assertEqual(data["employee_name"], "Ari Stone")

        serializer = ClientProfileSerializer(
            data={
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.doe@example.com",
                "phone": "0987654321",
                "employee": self.employee.id,
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.save().employee, self.employee)


class ServiceSerializerTest(SerializerTestBase):
    def test_service_serialization(self):
        data = ServiceSerializer(self.service).data
        self.assertEqual(data["name"], "service_1")
        self.assertEqual(data["name_display"], "Service 1")
        self.assertEqual(data["price"], "150.00")

    def test_service_rejects_negative_price(self):
        serializer = ServiceSerializer(
            data={"name": "service_2", "description": "Test", "price": "-1.00"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)


class AppointmentSerializerTest(SerializerTestBase):
    def test_appointment_serialization_and_deserialization(self):
        serializer = AppointmentSerializer(data=self.appointment_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)
        appointment = serializer.save()
        data = AppointmentSerializer(appointment).data
        self.assertEqual(data["client"]["id"], self.client_profile.id)
        self.assertEqual(data["employee"], self.employee.id)
        self.assertEqual(data["service"], "service_1")
        self.assertEqual(data["date"], "2026-08-25")

    def test_rejects_end_time_before_start(self):
        serializer = AppointmentSerializer(
            data=self.appointment_payload(time="15:00:00", end_time="14:00:00")
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("end_time", serializer.errors)

    def test_rejects_negative_price(self):
        serializer = AppointmentSerializer(data=self.appointment_payload(price="-1.00"))
        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)

    def test_rejects_deposit_above_price(self):
        serializer = AppointmentSerializer(
            data=self.appointment_payload(
                deposit_required=True,
                deposit_amount="151.00",
            )
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("deposit_amount", serializer.errors)


class NotificationSerializerTest(SerializerTestBase):
    def test_notification_serialization(self):
        notification = Notifications.objects.create(
            employee=self.employee,
            action="created",
        )
        data = NotificationSerializer(notification).data
        self.assertEqual(data["employee"], self.employee.id)
        self.assertEqual(data["employee_name"], "Ari Stone")
        self.assertEqual(data["status"], "pending")

    def test_invalid_status(self):
        serializer = NotificationSerializer(
            data={
                "employee": self.employee.id,
                "action": "created",
                "status": "invalid_status",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)

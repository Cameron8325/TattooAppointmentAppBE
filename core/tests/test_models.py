from datetime import date, time

from django.core.exceptions import ValidationError
from django.test import TestCase

from core.models import Appointment, ClientProfile, Notifications, Service, User


class ModelTestBase(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="artistuser",
            password="testpass123",
            role="employee",
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


class UserModelTest(ModelTestBase):
    def test_user_creation_and_password_hashing(self):
        self.assertEqual(self.employee.role, "employee")
        self.assertTrue(self.employee.check_password("testpass123"))
        self.assertNotEqual(self.employee.password, "testpass123")

    def test_username_is_required(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(username=None, password="testpass123")


class ClientProfileModelTest(ModelTestBase):
    def test_client_profile_creation(self):
        self.assertEqual(self.client_profile.employee, self.employee)
        self.assertEqual(str(self.client_profile), "John Doe")


class ServiceModelTest(ModelTestBase):
    def test_service_creation(self):
        self.assertEqual(self.service.name, "service_1")
        self.assertEqual(str(self.service), "Service 1")

    def test_service_rejects_negative_price(self):
        self.service.price = "-0.01"
        with self.assertRaises(ValidationError):
            self.service.full_clean()


class AppointmentModelTest(ModelTestBase):
    def make_appointment(self, **overrides):
        values = {
            "client": self.client_profile,
            "employee": self.employee,
            "service": self.service,
            "date": date(2026, 8, 25),
            "time": time(14, 0),
            "end_time": time(15, 0),
            "price": "150.00",
            "status": "pending",
            "notes": "Custom tattoo on forearm.",
        }
        values.update(overrides)
        return Appointment(**values)

    def test_appointment_creation(self):
        appointment = self.make_appointment()
        appointment.full_clean()
        appointment.save()
        self.assertEqual(appointment.employee, self.employee)
        self.assertEqual(
            str(appointment),
            f"Appointment for {self.client_profile} with {self.employee} on {appointment.date}",
        )

    def test_appointment_rejects_invalid_time_range(self):
        appointment = self.make_appointment(time=time(15, 0), end_time=time(14, 0))
        with self.assertRaises(ValidationError):
            appointment.full_clean()

    def test_appointment_rejects_negative_amounts(self):
        appointment = self.make_appointment(price="-1.00")
        with self.assertRaises(ValidationError):
            appointment.full_clean()


class NotificationsModelTest(ModelTestBase):
    def test_notification_creation_and_defaults(self):
        notification = Notifications.objects.create(
            employee=self.employee,
            action="created",
        )
        self.assertEqual(notification.status, "pending")
        self.assertIsNotNone(notification.timestamp)
        self.assertEqual(
            str(notification),
            f"Notification from {self.employee} - created (pending)",
        )

    def test_notification_status_choices(self):
        notification = Notifications(employee=self.employee, action="created")
        notification.status = "invalid_choice"
        with self.assertRaises(ValidationError):
            notification.full_clean()

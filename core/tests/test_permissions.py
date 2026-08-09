"""
Permission tests.

Rewritten 2026-07: the previous version targeted a pre-migration-0006 schema
(is_artist flag, artist FKs, Service.artist) and errored in setUp. Original
The original permission intents are preserved and now enforced.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Appointment, ClientProfile, Service, User


class PermissionTestBase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="testpass123", role="admin"
        )
        self.employee = User.objects.create_user(
            username="employee", password="testpass123", role="employee"
        )
        self.other_employee = User.objects.create_user(
            username="other_employee", password="testpass123", role="employee"
        )
        self.client_profile = ClientProfile.objects.create(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="1234567890",
            employee=self.employee,
        )
        self.service = Service.objects.create(
            name="service_1", description="A custom tattoo design.", price=150.00
        )
        self.appointment = Appointment.objects.create(
            client=self.client_profile,
            employee=self.employee,
            service=self.service,
            date="2026-08-15",
            time="16:00:00",
            end_time="17:00:00",
            price=150.00,
            status="pending",
            notes="Initial notes.",
        )
        self.client = APIClient()


class AnonymousAccessTest(PermissionTestBase):
    def test_anonymous_user_cannot_create_client_profile(self):
        response = self.client.post(
            reverse("clientprofile-list"),
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.doe@example.com",
                "phone": "0987654321",
                "employee": self.employee.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_create_appointment(self):
        response = self.client.post(
            reverse("appointment-list"),
            {
                "client_id": self.client_profile.id,
                "employee": self.employee.id,
                "service": "service_1",
                "date": "2026-08-20",
                "time": "14:00:00",
                "end_time": "15:00:00",
                "price": "150.00",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserEndpointPermissionTest(PermissionTestBase):
    """Phase 1: register/, users/, users/<pk>/."""

    def test_anonymous_cannot_register(self):
        response = self.client.post(
            reverse("register"),
            {"username": "intruder", "password": "hackme12345", "email": "x@x.com"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_register_users(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.post(
            reverse("register"),
            {"username": "newuser", "password": "testpass123", "email": "n@x.com"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_register_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("register"),
            {"username": "newuser", "password": "testpass123", "email": "n@x.com"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_employee_cannot_list_users(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employee_can_retrieve_self(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get(
            reverse("user-detail", kwargs={"pk": self.employee.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employee_cannot_retrieve_other_user(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get(
            reverse("user-detail", kwargs={"pk": self.other_employee.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_can_update_own_email(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.patch(
            reverse("user-detail", kwargs={"pk": self.employee.id}),
            {"email": "new@example.com"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employee_cannot_update_other_user(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.patch(
            reverse("user-detail", kwargs={"pk": self.other_employee.id}),
            {"email": "pwned@example.com"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_delete_users(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.delete(
            reverse("user-detail", kwargs={"pk": self.other_employee.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(pk=self.other_employee.id).exists())

    def test_employee_cannot_delete_self(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.delete(
            reverse("user-detail", kwargs={"pk": self.employee.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_retrieve_and_delete_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            reverse("user-detail", kwargs={"pk": self.employee.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(
            reverse("user-detail", kwargs={"pk": self.other_employee.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ObjectOwnershipTest(PermissionTestBase):
    """Service writes are admin-only and appointments are owner-scoped."""

    def test_employee_cannot_edit_service(self):
        self.client.force_authenticate(user=self.other_employee)
        response = self.client.put(
            reverse("service-detail", kwargs={"pk": self.service.id}),
            {
                "name": "service_1",
                "description": "Updated description.",
                "price": "200.00",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_appointment_cannot_be_modified_by_other_employee(self):
        self.client.force_authenticate(user=self.other_employee)
        response = self.client.patch(
            reverse("appointment-detail", kwargs={"pk": self.appointment.id}),
            {"status": "completed", "notes": "Hijacked notes."},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

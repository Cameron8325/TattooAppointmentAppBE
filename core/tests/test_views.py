from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Appointment, ClientProfile, Notifications, Service, User


class ViewTestBase(TestCase):
    def setUp(self):
        self.api = APIClient()
        self.admin = User.objects.create_user(
            username="admin",
            password="adminpass123",
            role="admin",
        )
        self.employee = User.objects.create_user(
            username="artistuser",
            password="testpass123",
            role="employee",
            first_name="Ari",
            last_name="Stone",
        )
        self.other_employee = User.objects.create_user(
            username="otherartist",
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
        self.appointment = Appointment.objects.create(
            client=self.client_profile,
            employee=self.employee,
            service=self.service,
            date=date.today() + timedelta(days=7),
            time=time(14, 0),
            end_time=time(15, 0),
            price="150.00",
            status="pending",
            notes="Forearm tattoo.",
        )

    def appointment_payload(self, **overrides):
        payload = {
            "client_id": self.client_profile.id,
            "employee": self.employee.id,
            "service": self.service.name,
            "date": (date.today() + timedelta(days=10)).isoformat(),
            "time": "16:00:00",
            "end_time": "17:00:00",
            "price": "150.00",
        }
        payload.update(overrides)
        return payload


class UserViewTest(ViewTestBase):
    def test_admin_can_list_users(self):
        self.api.force_authenticate(user=self.admin)
        response = self.api.get(reverse("user-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_employee_can_retrieve_self(self):
        self.api.force_authenticate(user=self.employee)
        response = self.api.get(
            reverse("user-detail", kwargs={"pk": self.employee.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "artistuser")


class ClientProfileViewTest(ViewTestBase):
    def test_client_profile_list_and_detail(self):
        self.api.force_authenticate(user=self.employee)
        response = self.api.get(reverse("clientprofile-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["first_name"], "John")

        response = self.api.get(
            reverse("clientprofile-detail", kwargs={"pk": self.client_profile.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["employee"], self.employee.id)


class ServiceViewTest(ViewTestBase):
    def test_employee_can_read_but_not_edit_services(self):
        self.api.force_authenticate(user=self.employee)
        response = self.api.get(reverse("service-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.api.patch(
            reverse("service-detail", kwargs={"pk": self.service.id}),
            {"price": "200.00"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AppointmentViewTest(ViewTestBase):
    def test_employee_only_lists_own_appointments(self):
        Appointment.objects.create(
            client=self.client_profile,
            employee=self.other_employee,
            service=self.service,
            date=date.today() + timedelta(days=8),
            time=time(10, 0),
            end_time=time(11, 0),
            price="100.00",
        )
        self.api.force_authenticate(user=self.employee)
        response = self.api.get(reverse("appointment-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in response.data], [self.appointment.id])

    def test_employee_creation_is_forced_to_self_and_pending(self):
        self.api.force_authenticate(user=self.employee)
        response = self.api.post(
            reverse("appointment-list"),
            self.appointment_payload(
                employee=self.other_employee.id,
                status="confirmed",
                requires_approval=False,
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        created = Appointment.objects.get(pk=response.data["id"])
        self.assertEqual(created.employee, self.employee)
        self.assertEqual(created.status, "pending")
        self.assertTrue(created.requires_approval)

    def test_rejects_negative_price(self):
        self.api.force_authenticate(user=self.employee)
        response = self.api.post(
            reverse("appointment-list"),
            self.appointment_payload(price="-1.00"),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data)

    def test_other_employee_cannot_retrieve_or_reschedule(self):
        self.api.force_authenticate(user=self.other_employee)
        detail = self.api.get(
            reverse("appointment-detail", kwargs={"pk": self.appointment.id})
        )
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

        reschedule = self.api.patch(
            reverse("reschedule-appointment", kwargs={"pk": self.appointment.id}),
            {"time": "17:00:00", "end_time": "18:00:00"},
        )
        self.assertEqual(reschedule.status_code, status.HTTP_404_NOT_FOUND)


class NotificationViewTest(ViewTestBase):
    def setUp(self):
        super().setUp()
        self.notification = Notifications.objects.create(
            employee=self.employee,
            appointment=self.appointment,
            action="created",
            status="pending",
        )

    def test_admin_can_review_and_approve_notification(self):
        self.api.force_authenticate(user=self.admin)
        response = self.api.get(reverse("recent-activity"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], self.notification.id)

        response = self.api.post(
            reverse("approve-notification", kwargs={"pk": self.notification.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.status, "approved")

    def test_employee_cannot_approve_notifications(self):
        self.api.force_authenticate(user=self.employee)
        response = self.api.post(
            reverse("approve-notification", kwargs={"pk": self.notification.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import User, ClientProfile, Service, Appointment, Notifications
from datetime import date, time


class UserViewTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.artist = User.objects.create_user(username='artistuser', password='testpass', is_artist=True)

    def test_user_list_view(self):
        """Test the user list view returns a list of users."""
        self.client.force_authenticate(user=self.artist)
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'artistuser')

    def test_user_detail_view(self):
        """Test the user detail view returns the correct user."""
        self.client.force_authenticate(user=self.artist)
        url = reverse('user-detail', kwargs={'pk': self.artist.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'artistuser')


class ClientProfileViewTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.artist = User.objects.create_user(username='artistuser', password='testpass', is_artist=True)
        self.client_profile = ClientProfile.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='1234567890',
            artist=self.artist
        )

    def test_client_profile_list_view(self):
        """Test the client profile list view returns all client profiles."""
        self.client.force_authenticate(user=self.artist)
        response = self.client.get(reverse('clientprofile-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['first_name'], 'John')

    def test_client_profile_detail_view(self):
        """Test the client profile detail view returns the correct profile."""
        self.client.force_authenticate(user=self.artist)
        url = reverse('clientprofile-detail', kwargs={'pk': self.client_profile.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')


class ServiceViewTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.artist = User.objects.create_user(username='artistuser', password='testpass', is_artist=True)
        self.service = Service.objects.create(
            name='Tattoo Design',
            description='A custom tattoo design.',
            price=150.00,
            artist=self.artist
        )

    def test_service_list_view(self):
        """Test the service list view returns all services."""
        self.client.force_authenticate(user=self.artist)
        response = self.client.get(reverse('service-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Tattoo Design')

    def test_service_detail_view(self):
        """Test the service detail view returns the correct service."""
        self.client.force_authenticate(user=self.artist)
        url = reverse('service-detail', kwargs={'pk': self.service.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Tattoo Design')


class AppointmentViewTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.artist = User.objects.create_user(username='artistuser', password='testpass', is_artist=True)
        self.client_profile = ClientProfile.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='1234567890',
            artist=self.artist
        )
        self.service = Service.objects.create(
            name='Tattoo Design',
            description='A custom tattoo design.',
            price=150.00,
            artist=self.artist
        )
        self.appointment = Appointment.objects.create(
            client=self.client_profile,
            artist=self.artist,
            service=self.service,
            date=date(2025, 1, 25),
            time=time(14, 0),
            status='pending',
            notes='Forearm tattoo.'
        )

    def test_appointment_list_view(self):
        """Test the appointment list view returns all appointments."""
        self.client.force_authenticate(user=self.artist)
        response = self.client.get(reverse('appointment-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'pending')

    def test_appointment_detail_view(self):
        """Test the appointment detail view returns the correct appointment."""
        self.client.force_authenticate(user=self.artist)
        url = reverse('appointment-detail', kwargs={'pk': self.appointment.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notes'], 'Forearm tattoo.')

class NotificationViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create an admin user and authenticate
        self.admin_user = User.objects.create_superuser(
            username='admin', password='adminpass', is_artist=False
        )
        self.client.login(username='admin', password='adminpass')

        # Create test notifications
        self.notification1 = Notifications.objects.create(
            employee=self.admin_user,
            action="Requested schedule change",
            status="pending"
        )
        self.notification2 = Notifications.objects.create(
            employee=self.admin_user,
            action="Canceled appointment",
            status="pending"
        )

    def test_recent_activity_view(self):
        """Test fetching recent notifications."""
        response = self.client.get('/api/recent-activity/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['action'], "Requested schedule change")

    def test_approve_notification_view(self):
        """Test approving a notification."""
        response = self.client.post(f'/api/recent-activity/{self.notification1.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification1.refresh_from_db()
        self.assertEqual(self.notification1.status, "approved")

    def test_decline_notification_view(self):
        """Test declining a notification."""
        response = self.client.post(f'/api/recent-activity/{self.notification2.id}/decline/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification2.refresh_from_db()
        self.assertEqual(self.notification2.status, "denied")

    def test_unauthorized_access(self):
        """Test that non-admin users cannot access the views."""
        non_admin_user = User.objects.create_user(
            username='testuser', password='testpass', is_artist=False
        )
        self.client.login(username='testuser', password='testpass')

        response = self.client.get('/api/recent-activity/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.post(f'/api/recent-activity/{self.notification1.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

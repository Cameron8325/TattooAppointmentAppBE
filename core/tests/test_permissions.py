from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase
from core.models import User, ClientProfile, Service, Appointment

class PermissionTest(TestCase):
    """
    Tests to ensure proper permissions are enforced for various actions.
    """

    def setUp(self):
        """
        Set up test users and data for permission tests.
        """
        self.artist = User.objects.create_user(username='artist', password='testpass', is_artist=True)
        self.other_artist = User.objects.create_user(username='other_artist', password='testpass', is_artist=True)
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
            date='2025-02-15',
            time='16:00:00',
            status='pending',
            notes='Initial notes.',
        )
        self.client = APIClient()

    def test_anonymous_user_cannot_create_client_profile(self):
        """
        Test that an anonymous user cannot create a client profile.
        """
        url = reverse('clientprofile-list')
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane.doe@example.com',
            'phone': '0987654321',
            'artist': self.artist.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_create_appointment(self):
        """
        Test that an anonymous user cannot create an appointment.
        """
        url = reverse('appointment-list')
        data = {
            'client': self.client_profile.id,
            'artist': self.artist.id,
            'service': self.service.id,
            'date': '2025-02-20',
            'time': '14:00:00',
            'status': 'pending',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_artist_cannot_edit_other_artist_service(self):
        """
        Test that an artist cannot edit another artist's service.
        """
        self.client.force_authenticate(user=self.other_artist)
        url = reverse('service-detail', kwargs={'pk': self.service.id})
        data = {
            'name': 'Updated Service',
            'description': 'Updated description.',
            'price': self.service.price,
            'artist': self.service.artist.id,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_appointment_cannot_be_modified_by_other_artist(self):
        """
        Test that another artist cannot modify an appointment.
        """
        self.client.force_authenticate(user=self.other_artist)
        url = reverse('appointment-detail', kwargs={'pk': self.appointment.id})
        data = {
            'client': self.appointment.client.id,
            'artist': self.appointment.artist.id,
            'service': self.appointment.service.id,
            'date': str(self.appointment.date),
            'time': str(self.appointment.time),
            'status': 'completed',
            'notes': 'Updated notes for the appointment.',
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

from django.test import TestCase
from core.models import User, ClientProfile, Service, Appointment
from core.serializers import (
    UserSerializer,
    ClientProfileSerializer,
    ServiceSerializer,
    AppointmentSerializer,
)
from datetime import date, time

class UserSerializerTest(TestCase):
    """
    Test the UserSerializer to ensure correct serialization and deserialization.
    """

    def setUp(self):
        """
        Set up a test user for serialization tests.
        """
        self.user = User.objects.create_user(username='testuser', password='testpass', is_artist=True)

    def test_user_serialization(self):
        """
        Test that the user model serializes correctly.
        """
        serializer = UserSerializer(instance=self.user)
        expected_data = {'id': self.user.id, 'username': 'testuser', 'email': '', 'is_artist': True}
        self.assertEqual(serializer.data, expected_data)

class ClientProfileSerializerTest(TestCase):
    """
    Test the ClientProfileSerializer for correct data handling.
    """

    def setUp(self):
        """
        Set up a test artist and client profile for serialization tests.
        """
        self.artist = User.objects.create_user(username='artistuser', password='testpass', is_artist=True)
        self.client_profile = ClientProfile.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='1234567890',
            artist=self.artist
        )

    def test_client_profile_serialization(self):
        """
        Test that the client profile model serializes correctly.
        """
        serializer = ClientProfileSerializer(instance=self.client_profile)
        expected_data = {
            'id': self.client_profile.id,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'artist': self.artist.id,
        }
        self.assertEqual(serializer.data, expected_data)

    def test_client_profile_deserialization(self):
        """
        Test that client profile data deserializes and validates correctly.
        """
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane.doe@example.com',
            'phone': '0987654321',
            'artist': self.artist.id,
        }
        serializer = ClientProfileSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        client_profile = serializer.save()
        self.assertEqual(client_profile.artist, self.artist)

class ServiceSerializerTest(TestCase):
    """
    Test the ServiceSerializer for correct data handling.
    """

    def setUp(self):
        """
        Set up a test artist for service tests.
        """
        self.artist = User.objects.create_user(username='artistuser', password='testpass', is_artist=True)

    def test_service_serialization(self):
        """
        Test that the service model serializes correctly.
        """
        service = Service.objects.create(
            name='Tattoo Design',
            description='A custom tattoo design.',
            price=150.00,
            artist=self.artist
        )
        serializer = ServiceSerializer(instance=service)
        expected_data = {
            'id': service.id,
            'name': 'Tattoo Design',
            'description': 'A custom tattoo design.',
            'price': '150.00',
            'artist': self.artist.id,
        }
        self.assertEqual(serializer.data, expected_data)

    def test_service_deserialization(self):
        """
        Test that service data deserializes and validates correctly.
        """
        data = {
            'name': 'Piercing',
            'description': 'Earlobe piercing',
            'price': '50.00',
            'artist': self.artist.id,
        }
        serializer = ServiceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        service = serializer.save()
        self.assertEqual(service.artist, self.artist)

class AppointmentSerializerTest(TestCase):
    """
    Test the AppointmentSerializer for correct data handling.
    """

    def setUp(self):
        """
        Set up test data for appointment tests.
        """
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

    def test_appointment_serialization(self):
        """
        Test that the appointment model serializes correctly.
        """
        appointment = Appointment.objects.create(
            client=self.client_profile,
            artist=self.artist,
            service=self.service,
            date=date(2025, 1, 25),
            time=time(14, 0),
            status='pending',
            notes='Forearm tattoo.'
        )
        serializer = AppointmentSerializer(instance=appointment)
        expected_data = {
            'id': appointment.id,
            'client': self.client_profile.id,
            'artist': self.artist.id,
            'service': self.service.id,
            'date': str(appointment.date),
            'time': str(appointment.time),
            'status': 'pending',
            'notes': 'Forearm tattoo.',
        }
        self.assertEqual(serializer.data, expected_data)

    def test_appointment_deserialization(self):
        """
        Test that appointment data deserializes and validates correctly.
        """
        data = {
            'client': self.client_profile.id,
            'artist': self.artist.id,
            'service': self.service.id,
            'date': '2025-02-15',
            'time': '16:00:00',
            'status': 'confirmed',
            'notes': 'Leg tattoo.',
        }
        serializer = AppointmentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        appointment = serializer.save()
        self.assertEqual(appointment.artist, self.artist)

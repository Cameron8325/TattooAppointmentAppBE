from django.test import TestCase
from core.models import User, ClientProfile, Service, Appointment
from datetime import date, time

class UserModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', is_artist=True)

    def test_user_creation(self):
        """Test that a user is created successfully."""
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.check_password('testpass'))
        self.assertTrue(self.user.is_artist)

    def test_username_is_required(self):
        """Test that username is required to create a user."""
        with self.assertRaises(ValueError):
            User.objects.create_user(username=None, password='testpass')

    def test_password_is_hashed(self):
        """Test that the password is stored as a hash, not plain text."""
        self.assertNotEqual(self.user.password, 'testpass')


class ClientProfileModelTest(TestCase):

    def setUp(self):
        self.artist = User.objects.create_user(username='artistuser', password='testpass', is_artist=True)
        self.client_profile = ClientProfile.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='1234567890',
            artist=self.artist
        )

    def test_client_profile_creation(self):
        """Test that a client profile is created successfully."""
        self.assertEqual(self.client_profile.first_name, 'John')
        self.assertEqual(self.client_profile.last_name, 'Doe')
        self.assertEqual(self.client_profile.email, 'john.doe@example.com')
        self.assertEqual(self.client_profile.phone, '1234567890')
        self.assertEqual(self.client_profile.artist, self.artist)

    def test_client_profile_string_representation(self):
        """Test the string representation of the client profile."""
        self.assertEqual(str(self.client_profile), 'John Doe')


class ServiceModelTest(TestCase):

    def setUp(self):
        self.artist = User.objects.create_user(username='artistuser', password='testpass', is_artist=True)
        self.service = Service.objects.create(
            name='Tattoo Design',
            description='A custom tattoo design.',
            price=150.00,
            artist=self.artist
        )

    def test_service_creation(self):
        """Test that a service is created successfully."""
        self.assertEqual(self.service.name, 'Tattoo Design')
        self.assertEqual(self.service.description, 'A custom tattoo design.')
        self.assertEqual(self.service.price, 150.00)
        self.assertEqual(self.service.artist, self.artist)

    def test_service_string_representation(self):
        """Test the string representation of the service."""
        self.assertEqual(str(self.service), 'Tattoo Design')


class AppointmentModelTest(TestCase):

    def setUp(self):
        self.artist = User.objects.create_user(username='artistuser', password='testpass', is_artist=True)
        self.client = ClientProfile.objects.create(
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
            client=self.client,
            artist=self.artist,
            service=self.service,
            date=date(2025, 1, 25),
            time=time(14, 0),
            status='pending',
            notes='Custom tattoo on forearm.'
        )

    def test_appointment_creation(self):
        """Test that an appointment is created successfully."""
        self.assertEqual(self.appointment.client, self.client)
        self.assertEqual(self.appointment.artist, self.artist)
        self.assertEqual(self.appointment.service, self.service)
        self.assertEqual(self.appointment.date, date(2025, 1, 25))
        self.assertEqual(self.appointment.time, time(14, 0))
        self.assertEqual(self.appointment.status, 'pending')
        self.assertEqual(self.appointment.notes, 'Custom tattoo on forearm.')

    def test_appointment_string_representation(self):
        """Test the string representation of the appointment."""
        self.assertEqual(
            str(self.appointment),
            f"Appointment for {self.client} with {self.artist} on {self.appointment.date}"
        )

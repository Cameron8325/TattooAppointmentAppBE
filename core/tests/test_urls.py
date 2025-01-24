from django.test import SimpleTestCase
from django.urls import reverse, resolve
from core import views

class UrlsTest(SimpleTestCase):
    """
    Test the URL configuration to ensure it resolves to the correct views.
    """

    def test_user_list_url(self):
        """
        Test the user list URL resolves correctly.
        """
        url = reverse('user-list')
        self.assertEqual(resolve(url).func.view_class, views.UserListView)

    def test_user_detail_url(self):
        """
        Test the user detail URL resolves correctly.
        """
        url = reverse('user-detail', kwargs={'pk': 1})
        self.assertEqual(resolve(url).func.view_class, views.UserDetailView)

    def test_client_profile_list_url(self):
        """
        Test the client profile list URL resolves correctly.
        """
        url = reverse('clientprofile-list')
        self.assertEqual(resolve(url).func.view_class, views.ClientProfileListView)

    def test_client_profile_detail_url(self):
        """
        Test the client profile detail URL resolves correctly.
        """
        url = reverse('clientprofile-detail', kwargs={'pk': 1})
        self.assertEqual(resolve(url).func.view_class, views.ClientProfileDetailView)

    def test_service_list_url(self):
        """
        Test the service list URL resolves correctly.
        """
        url = reverse('service-list')
        self.assertEqual(resolve(url).func.view_class, views.ServiceListView)

    def test_service_detail_url(self):
        """
        Test the service detail URL resolves correctly.
        """
        url = reverse('service-detail', kwargs={'pk': 1})
        self.assertEqual(resolve(url).func.view_class, views.ServiceDetailView)

    def test_appointment_list_url(self):
        """
        Test the appointment list URL resolves correctly.
        """
        url = reverse('appointment-list')
        self.assertEqual(resolve(url).func.view_class, views.AppointmentListView)

    def test_appointment_detail_url(self):
        """
        Test the appointment detail URL resolves correctly.
        """
        url = reverse('appointment-detail', kwargs={'pk': 1})
        self.assertEqual(resolve(url).func.view_class, views.AppointmentDetailView)

    def test_recent_activity_url(self):
        """
        Test the recent activity URL resolves correctly.
        """
        url = reverse('recent-activity')
        self.assertEqual(resolve(url).func.view_class, views.RecentActivityView)

    def test_approve_notification_url(self):
        """
        Test the approve notification URL resolves correctly.
        """
        url = reverse('approve-notification', kwargs={'pk': 1})
        self.assertEqual(resolve(url).func.view_class, views.ApproveNotificationView)

    def test_decline_notification_url(self):
        """
        Test the decline notification URL resolves correctly.
        """
        url = reverse('decline-notification', kwargs={'pk': 1})
        self.assertEqual(resolve(url).func.view_class, views.DeclineNotificationView)

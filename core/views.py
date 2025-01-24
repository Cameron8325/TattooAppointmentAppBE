from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from .models import User, ClientProfile, Service, Appointment, Notifications
from .serializers import (
    UserSerializer,
    ClientProfileSerializer,
    ServiceSerializer,
    AppointmentSerializer,
    NotificationSerializer
)

# User Views
class UserListView(ListCreateAPIView):
    """
    Handles listing all users and creating new users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class UserDetailView(RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, or deleting a specific user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


# Client Profile Views
class ClientProfileListView(ListCreateAPIView):
    """
    Handles listing and creating client profiles. Only authenticated artists can create profiles.
    """
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Restrict creation of client profiles to artists.
        """
        if not self.request.user.is_artist:
            raise PermissionDenied("Only artists can create client profiles.")
        serializer.save()


class ClientProfileDetailView(RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, or deleting a specific client profile.
    """
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]


# Service Views
class ServiceListView(ListCreateAPIView):
    """
    Handles listing all services and creating new ones. Only authenticated users can create services.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]


class ServiceDetailView(RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, or deleting a specific service. Artists cannot modify services created by others.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        """
        Restrict updates to services owned by the authenticated artist.
        """
        if self.request.user != serializer.instance.artist:
            raise PermissionDenied("You cannot modify another artist's service.")
        serializer.save()


# Appointment Views
class AppointmentListView(ListCreateAPIView):
    """
    Handles listing all appointments and creating new ones. Only authenticated users can create appointments.
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Restrict creation of appointments to authenticated users.
        """
        if not self.request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to create appointments.")
        serializer.save()


class AppointmentDetailView(RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, or deleting a specific appointment. Artists cannot modify appointments they don't own.
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        """
        Restrict updates to appointments owned by the authenticated artist.
        """
        if self.request.user != serializer.instance.artist:
            raise PermissionDenied("You cannot modify another artist's appointment.")
        serializer.save()

#Notification Views
class RecentActivityView(ListAPIView):
    """
    Handles fetching and listing all notifications by timestamps
    """
    queryset = Notifications.objects.all().order_by('-timestamp')
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser] #Only admins can access this view

class ApproveNotificationView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        notification = get_object_or_404(Notifications, pk=pk)
        notification.status = 'approved'
        notification.save()
        return Response({"message": "Notification approved successfully."}, status=200)

class DeclineNotificationView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        notification = get_object_or_404(Notifications, pk=pk)  # Corrected model name
        notification.status = 'denied'
        notification.save()
        return Response({"message": "Notification declined successfully."}, status=200)


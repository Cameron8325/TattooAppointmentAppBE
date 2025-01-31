from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate, login, logout
from datetime import date, timedelta
from .models import User, ClientProfile, Service, Appointment, Notifications
from .serializers import (
    UserSerializer,
    ClientProfileSerializer,
    ServiceSerializer,
    AppointmentSerializer,
    NotificationSerializer
)

# Authentication Views
class RegisterView(generics.CreateAPIView):
    """
    Handles user registration.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)  # ✅ Log the user in using Django's session authentication
            response = Response({
                "message": "Login successful",
                "user": {"id": user.id, "username": user.username}
            }, status=status.HTTP_200_OK)
            response.set_cookie("csrftoken", get_token(request), httponly=False)  # ✅ Ensure CSRF token is set
            return response

        return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class CSRFTokenView(APIView):
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class LogoutView(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            logout(request)
            response = Response({"message": "Logged out"}, status=status.HTTP_200_OK)
            response.delete_cookie("sessionid")  # Ensure the session cookie is removed
            response.delete_cookie("csrftoken")  # Remove CSRF token if needed
            return response
        return Response({"error": "User not logged in"}, status=status.HTTP_401_UNAUTHORIZED)



class UserView(APIView):
    permission_classes = [IsAuthenticated]  # ✅ Ensures only authenticated users can access

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# User Management Views
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
    Handles listing all services and creating new ones.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

class ServiceDetailView(RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, or deleting a specific service.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

# Appointment Views
class AppointmentListView(ListCreateAPIView):
    """
    Handles listing all appointments and creating new ones.
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

class AppointmentDetailView(RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, or deleting a specific appointment.
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

class AppointmentOverviewView(APIView):
    """
    Returns an overview of appointment data.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filter_param = request.query_params.get("filter", None)
        queryset = Appointment.objects.all()

        if filter_param == "today":
            queryset = queryset.filter(date=date.today())
        elif filter_param == "this_week":
            start_of_week = date.today() - timedelta(days=date.today().weekday())
            end_of_week = start_of_week + timedelta(days=6)
            queryset = queryset.filter(date__range=[start_of_week, end_of_week])

        data = {
            "total": queryset.count(),
            "completed": queryset.filter(status="completed").count(),
            "pending": queryset.filter(status="pending").count(),
            "canceled": queryset.filter(status="canceled").count(),
        }

        return Response(data)

class RescheduleAppointmentView(APIView):
    """
    Allows users to reschedule appointments by updating the date and time.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        data = request.data

        allowed_updates = {key: data[key] for key in ["date", "time"] if key in data}
        if not allowed_updates:
            return Response({"error": "No valid fields provided for update."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AppointmentSerializer(appointment, data=allowed_updates, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Notification Views
class RecentActivityView(ListAPIView):
    """
    Handles fetching and listing all notifications by timestamps.
    """
    queryset = Notifications.objects.all().order_by("-timestamp")
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser]  # Only admins can access this view

class ApproveNotificationView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        notification = get_object_or_404(Notifications, pk=pk)
        notification.status = "approved"
        notification.save()
        return Response({"message": "Notification approved successfully."}, status=200)

class DeclineNotificationView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        notification = get_object_or_404(Notifications, pk=pk)
        notification.status = "denied"
        notification.save()
        return Response({"message": "Notification declined successfully."}, status=200)

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate, login, logout, get_user_model
from datetime import date, timedelta
from .models import ClientProfile, Service, Appointment, Notifications
from .serializers import (
    UserSerializer,
    ClientProfileSerializer,
    ServiceSerializer,
    AppointmentSerializer,
    NotificationSerializer
)

# ✅ Get the custom user model
User = get_user_model()

# 🔹 Authentication Views
class RegisterView(generics.CreateAPIView):
    """
    Handles user registration.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

class LoginView(APIView):
    """
    Handles user login.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        print(f"🚀 Attempting login for: {username}")  # Debugging print

        user = authenticate(username=username, password=password)

        if user:
            print(f"✅ Authentication successful for: {username}")  # Debugging print
            login(request, user)
            response = Response({
                "message": "Login successful",
                "user": {"id": user.id, "username": user.username, "role": user.role}
            }, status=status.HTTP_200_OK)
            response.set_cookie("csrftoken", get_token(request), httponly=False)  # Ensure CSRF token is set
            return response

        print(f"❌ Authentication failed for: {username}")  # Debugging print
        return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class CSRFTokenView(APIView):
    """
    Provides CSRF token.
    """
    permission_classes = [AllowAny]  # ✅ Allow anyone to fetch the CSRF token

    @method_decorator(csrf_exempt)  # ✅ Exempt this view from CSRF protection
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class LogoutView(APIView):
    """
    Handles user logout.
    """
    def post(self, request):
        if request.user.is_authenticated:
            logout(request)
            response = Response({"message": "Logged out"}, status=status.HTTP_200_OK)
            response.delete_cookie("sessionid")  # Ensure session cookie is removed
            response.delete_cookie("csrftoken")  # Remove CSRF token if needed
            return response
        return Response({"error": "User not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

class UserView(APIView):
    """
    Returns user details for authenticated users.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

# 🔹 User Management Views
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

# 🔹 Client Profile Views
class ClientProfileListView(ListCreateAPIView):
    """
    Handles listing and creating client profiles. Only employees can create profiles.
    """
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Restrict creation of client profiles to employees and admins.
        """
        if self.request.user.role not in ["employee", "admin"]:  # Check for both roles
            raise PermissionDenied("Only employees and admins can create client profiles.")
        serializer.save()


class ClientProfileDetailView(RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, or deleting a specific client profile.
    """
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]

# 🔹 Service Views
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

class AppointmentListView(ListCreateAPIView):
    """
    Handles listing all appointments and creating new ones.
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Appointment.objects.all()
        if user.role == "employee":
            return Appointment.objects.filter(client__employee=user)
        return Appointment.objects.filter(employee=user)

    def perform_create(self, serializer):
        # Simply let the serializer handle client creation/lookup.
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
    Allows users to reschedule appointments while preventing double-booking.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        data = request.data

        new_date = data.get("date", appointment.date)
        new_time = data.get("time", appointment.time)

        # ✅ Prevent double-booking
        conflict = Appointment.objects.filter(
            employee=appointment.employee, date=new_date, time=new_time
        ).exclude(id=appointment.id).exists()

        if conflict:
            return Response({"error": "This employee is already booked at this time."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AppointmentSerializer(appointment, data={"date": new_date, "time": new_time}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 🔹 Notification Views
class RecentActivityView(ListAPIView):
    """
    Allows admins to see all notifications and employees to see their own requests.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]  # Allow both admins and employees

    def get_queryset(self):
        user = self.request.user

        if user.role == "admin":
            return Notifications.objects.all().order_by("-timestamp")  # Admins see all notifications

        return Notifications.objects.filter(employee=user).order_by("-timestamp")  # Employees see their own


class ApproveNotificationView(APIView):
    """
    Allows an admin to approve a notification.
    """
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        """
        When a manager approves an appointment:
        ✅ The appointment is confirmed.
        ✅ The notification is marked as approved.
        ✅ The employee is notified.
        """
        notification = get_object_or_404(Notifications, pk=pk)

        # ✅ Update the appointment status
        if notification.appointment:
            notification.appointment.status = "confirmed"
            notification.appointment.requires_approval = False
            notification.appointment.save()

        # ✅ Update the notification
        notification.status = "approved"
        notification.save()

        # ✅ Notify the employee
        Notifications.objects.create(
            employee=notification.appointment.client.employee,
            appointment=notification.appointment,
            action="approved",
            status="approved"
        )

        return Response({"message": "Appointment approved successfully."}, status=200)


class DeclineNotificationView(APIView):
    """
    Allows an admin to decline a notification.
    """
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        """
        When a manager denies an appointment:
        ✅ The appointment is canceled.
        ✅ The notification is marked as denied.
        ✅ The employee is notified.
        """
        notification = get_object_or_404(Notifications, pk=pk)

        # ✅ Update the appointment status to canceled
        if notification.appointment:
            notification.appointment.status = "canceled"
            notification.appointment.requires_approval = False
            notification.appointment.save()

        # ✅ Update the notification
        notification.status = "denied"
        notification.save()

        # ✅ Notify the employee
        Notifications.objects.create(
            employee=notification.appointment.client.employee,
            appointment=notification.appointment,
            action="denied",
            status="denied"
        )

        return Response({"message": "Appointment request denied."}, status=200)


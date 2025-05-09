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
from django.utils.timezone import now
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Sum
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
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        archived = self.request.query_params.get("archived")
        employee = self.request.query_params.get("employee")

        if user.role == "admin":
            if archived and archived.lower() == "true":
                qs = Appointment.objects.filter(date__lt=date.today())
            else:
                qs = Appointment.objects.filter(date__gte=date.today())

            if employee:
                qs = qs.filter(employee__id=employee)

            return qs

        if user.role == "employee":
            if archived and archived.lower() == "true":
                qs = Appointment.objects.filter(employee=user, date__lt=date.today())
            else:
                qs = Appointment.objects.filter(employee=user, date__gte=date.today())

            return qs


    def perform_create(self, serializer):
        appointment = serializer.save()
        # Only create a notification if the request comes from an employee (non-admin)
        if self.request.user.role != "admin":
            Notifications.objects.create(
                employee=self.request.user,
                appointment=appointment,
                action="created",
                changes={
                    "date": str(appointment.date),
                    "time": str(appointment.time),
                    "end_time": str(appointment.end_time),
                    "price": str(appointment.price),
                    "service": appointment.service.name,
                    "notes": appointment.notes,
                }
            )


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
            "no_show": queryset.filter(status="no_show").count(),
        }

        return Response(data)

class RescheduleAppointmentView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        data = request.data
        user = request.user

        # Handle direct status change (e.g., to "completed" or "no_show")
        new_status = data.get("status")
        if new_status in ["completed", "no_show"]:
            previous_status = appointment.status
            appointment.status = new_status
            appointment.requires_approval = False
            appointment.save()

            if new_status == "no_show":
                Notifications.objects.create(
                    employee=user,
                    appointment=appointment,
                    action="no_show",
                    changes={"status": {"old": previous_status, "new": "no_show"}},
                    status="pending"
                )

            return Response({"message": f"Appointment marked as {new_status}."}, status=status.HTTP_200_OK)

        # Capture snapshot of existing values
        previous_data = {
            "date": str(appointment.date),
            "time": str(appointment.time),
            "end_time": str(appointment.end_time),
            "price": str(appointment.price),
            "service": appointment.service.name,
            "notes": appointment.notes,
        }

        # Get the new values (fallback to current)
        new_data = {
            "date": data.get("date", str(appointment.date)),
            "time": data.get("time", str(appointment.time)),
            "end_time": data.get("end_time", str(appointment.end_time)),
            "price": data.get("price", str(appointment.price)),
            "service": data.get("service", appointment.service.name),
            "notes": data.get("notes", appointment.notes),
        }

        # Compute changes for diff
        diff = {}
        for key in previous_data:
            if previous_data[key] != new_data[key]:
                diff[key] = {"old": previous_data[key], "new": new_data[key]}

        # ✅ Different logic for Admin vs Employee
        if user.role == "admin":
            updated_data = {
                "date": data.get("date", appointment.date),
                "time": data.get("time", appointment.time),
                "end_time": data.get("end_time", appointment.end_time),
                "price": data.get("price", appointment.price),
                "service": data.get("service", appointment.service.name),
                "notes": data.get("notes", appointment.notes),
                "status": "confirmed",
                "requires_approval": False,
                "client_id": data.get("client_id", appointment.client.id)
            }
        else:
            updated_data = {
                "date": data.get("date", appointment.date),
                "time": data.get("time", appointment.time),
                "end_time": data.get("end_time", appointment.end_time),
                "price": data.get("price", appointment.price),
                "service": data.get("service", appointment.service.name),
                "notes": data.get("notes", appointment.notes),
                "status": "pending",
                "requires_approval": True,
                "client_id": data.get("client_id", appointment.client.id)
            }

        serializer = AppointmentSerializer(appointment, data=updated_data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # 🔔 Create or update notification only if not admin
            if user.role != "admin":
                existing_notification = Notifications.objects.filter(
                    appointment=appointment,
                    employee=user,
                    action="updated",
                    status="pending"
                ).first()

                if existing_notification:
                    existing_changes = existing_notification.changes or {}
                    existing_changes.update(diff)
                    existing_notification.changes = existing_changes
                    existing_notification.timestamp = now()
                    existing_notification.save()
                else:
                    Notifications.objects.create(
                        employee=user,
                        appointment=appointment,
                        action="updated",
                        changes=diff,
                        previous_details=previous_data,
                        status="pending"
                    )

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 🔹 Notification Views
class RecentActivityView(ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Auto-delete notifications older than 30 days
        threshold_date = now() - timedelta(days=30)
        Notifications.objects.filter(timestamp__lt=threshold_date).delete()

        if user.role == "admin":
            # Exclude notifications where the employee is the current admin
            return Notifications.objects.exclude(employee=user).order_by("-timestamp")
        return Notifications.objects.filter(employee=user).order_by("-timestamp")


class ApproveNotificationView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        notification = get_object_or_404(Notifications, pk=pk)

        if notification.appointment:
            notification.appointment.status = "confirmed"
            notification.appointment.requires_approval = False
            notification.appointment.save()

        # Clear the previous_details snapshot now that the appointment is confirmed.
        notification.previous_details = None
        notification.status = "approved"
        notification.save()

        return Response({"message": "Appointment approved successfully."}, status=200)


class DeclineNotificationView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        notification = get_object_or_404(Notifications, pk=pk)
        if notification.appointment:
            if notification.previous_details:
                # Revert appointment to its previous details
                appointment = notification.appointment
                pd = notification.previous_details
                appointment.date = pd.get("date", appointment.date)
                appointment.time = pd.get("time", appointment.time)
                appointment.end_time = pd.get("end_time", appointment.end_time)
                appointment.price = pd.get("price", appointment.price)
                # Look up the service by its name stored in previous_details
                service_name = pd.get("service")
                if service_name:
                    service_obj = Service.objects.filter(name=service_name).first()
                    if service_obj:
                        appointment.service = service_obj
                appointment.notes = pd.get("notes", appointment.notes)
                appointment.status = "confirmed"  # Revert to confirmed (or your desired default)
                appointment.requires_approval = False
                appointment.save()
            else:
                # For new appointments (with no previous details), cancel the appointment
                appointment = notification.appointment
                appointment.status = "canceled"
                appointment.requires_approval = False
                appointment.save()
        # Mark the notification as denied
        notification.status = "denied"
        notification.save()

        return Response({"message": "Appointment request denied."}, status=200)

class DeleteNotificationView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        notification = get_object_or_404(Notifications, pk=pk)

        # If it's a change request and has previous details, revert appointment
        if notification.action == "updated" and notification.previous_details:
            appointment = notification.appointment
            prev_details = notification.previous_details

            # Restore previous values
            appointment.date = prev_details.get("date", appointment.date)
            appointment.time = prev_details.get("time", appointment.time)
            appointment.end_time = prev_details.get("end_time", appointment.end_time)
            appointment.price = prev_details.get("price", appointment.price)

            # Restore service if it was changed
            service_name = prev_details.get("service")
            if service_name:
                service_obj = Service.objects.filter(name=service_name).first()
                if service_obj:
                    appointment.service = service_obj

            appointment.notes = prev_details.get("notes", appointment.notes)

            # Reset status since the request is no longer valid
            appointment.status = "confirmed"
            appointment.requires_approval = False
            appointment.save()

        # Delete the notification
        notification.delete()
        return Response({"message": "Notification deleted successfully"}, status=204)

class KeyMetrics(APIView):
    def get(self, request):
        queryset = Appointment.objects.filter(status="completed")
        range_param = request.query_params.get("range")
        month_param = request.query_params.get("month")

        # Last 7 or 30 Days Range
        if range_param == "last_7_days":
            start = date.today() - timedelta(days=7)
            queryset = queryset.filter(date__gte=start)
        elif range_param == "last_30_days":
            start = date.today() - timedelta(days=30)
            queryset = queryset.filter(date__gte=start)

        # Specific Month Filter (e.g., 2025-04)
        elif month_param:
            try:
                year, month = map(int, month_param.split("-"))
                start = date(year, month, 1)
                if month == 12:
                    end = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end = date(year, month + 1, 1) - timedelta(days=1)
                queryset = queryset.filter(date__range=[start, end])
            except ValueError:
                pass  # Invalid month format, fallback to no filter

        # Calculate metrics
        total_rev = queryset.aggregate(total_revenue=Sum("price"))["total_revenue"]
        total_appts = queryset.count()
        total_clients = queryset.values("client").distinct().count()

        return Response({
            "total_revenue": total_rev,
            "total_appointments": total_appts,
            "clients_served": total_clients
        })


class BillingSummaryView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        # Extract user-provided inputs
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        month = request.data.get("month")
        year = request.data.get("year")
        fee_type = request.data.get("fee_type")
        fee_value = request.data.get("fee_value")

        # Validate fee input
        if not fee_type or fee_value is None:
            return Response({"error": "Missing fee_type or fee_value."}, status=400)

        try:
            fee_value = Decimal(str(fee_value))
        except Exception:
            return Response({"error": "Fee value must be numeric."}, status=400)

        # Resolve date range
        if month and year:
            try:
                month = int(month)
                year = int(year)
                start_date = date(year, month, 1)
                if month == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, month + 1, 1) - timedelta(days=1)
            except ValueError:
                return Response({"error": "Invalid month or year provided."}, status=400)
        elif not start_date or not end_date:
            today = date.today()
            start_date = date(today.year, today.month, 1)
            end_date = today

        # Query appointments
        queryset = Appointment.objects.filter(status="completed", date__range=[start_date, end_date])
        shop_total_revenue = queryset.aggregate(Sum("price"))['price__sum'] or Decimal('0')
        shop_total_appointments = queryset.count()
        shop_total_earnings = Decimal('0')  # Track total shop earnings

        report_data = []
        employee_ids = queryset.values_list("employee", flat=True).distinct()

        for employee_id in employee_ids:
            employee_appts = queryset.filter(employee__id=employee_id)
            employee_total = employee_appts.aggregate(Sum("price"))['price__sum'] or Decimal('0')

            if fee_type == "flat":
                fee_amount = fee_value * employee_appts.count()
            elif fee_type == "percentage":
                fee_amount = employee_total * (fee_value / Decimal('100'))
            else:
                fee_amount = Decimal('0')

            shop_total_earnings += fee_amount  # Add to shop earnings total

            total_employee_revenue = employee_total - fee_amount

            employee_data = {
                "employee_id": employee_id,
                "total_earned": float(employee_total),
                "shop_fee": float(fee_amount),
                "net_payout": float(total_employee_revenue),
                "total_appointments": employee_appts.count(),
                "appointments": [
                    {
                        "client_name": f"{appt.client.first_name} {appt.client.last_name}",
                        "date": appt.date.strftime("%Y-%m-%d"),
                        "price": float(appt.price),
                        "shop_cut": float(fee_value) if fee_type == "flat" else float(appt.price * (fee_value / Decimal('100'))),
                        "artist_cut": float(appt.price - (fee_value if fee_type == "flat" else appt.price * (fee_value / Decimal('100')))),
                    }
                    for appt in employee_appts.order_by("date")
                ]
            }

            report_data.append(employee_data)

        # Return the full report with added earnings
        return Response({
            "shop_total_revenue": float(shop_total_revenue),
            "shop_total_appointments": shop_total_appointments,
            "shop_total_earnings": float(shop_total_earnings),
            "report": report_data
        })

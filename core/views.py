from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsAdmin, IsAdminOrReadOnly, IsOwnerOrAdmin, user_is_admin
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils.timezone import now, localdate
from django.db import transaction
from django.conf import settings
from .booking_workflow import lock_artists, update_booking, review_booking
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum, Count
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
    Handles user registration. Admin-only: this is an internal tool;
    accounts are provisioned by the shop admin, not self-service.
    """
    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = UserSerializer

class LoginView(APIView):
    """
    Handles user login.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            response = Response({
                "message": "Login successful",
                "user": {"id": user.id, "username": user.username, "role": user.role}
            }, status=status.HTTP_200_OK)
            response.set_cookie("csrftoken", get_token(request), httponly=False)  # Ensure CSRF token is set
            return response

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
    Handles listing all users and creating new users. Admin-only.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get('role')
        return queryset.filter(role=role) if role in ('admin', 'employee') else queryset


class UserDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve/update: the user themselves or an admin.
    Delete: admin only.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrAdmin]

    def delete(self, request, *args, **kwargs):
        if not user_is_admin(request.user):
            raise PermissionDenied("Administrator access required to delete users.")
        if self.get_object().pk == request.user.pk:
            raise ValidationError({'error': 'You cannot delete the account you are signed in with.'})
        if getattr(settings, 'DEMO_MODE', False) and self.get_object().username in settings.DEMO_LOGIN_NAMES:
            raise ValidationError({'error':'Shared demo sign-in accounts cannot be deleted.'})
        return super().delete(request, *args, **kwargs)

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
    permission_classes = [IsAdminOrReadOnly]

class ServiceDetailView(RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, or deleting a specific service.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAdminOrReadOnly]

class AppointmentListView(ListCreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        params = self.request.query_params
        queryset = Appointment.objects.all()
        if not user_is_admin(self.request.user):
            queryset = queryset.filter(employee=self.request.user)
        elif params.get('employee'):
            queryset = queryset.filter(employee_id=params['employee'])
        start, end = params.get('start_date'), params.get('end_date')
        if start or end:
            try:
                start, end = date.fromisoformat(start), date.fromisoformat(end)
            except (TypeError, ValueError):
                raise ValidationError({'date': 'Provide both start_date and end_date as YYYY-MM-DD.'})
            if start > end:
                raise ValidationError({'date': 'Start date must not be after end date.'})
            queryset = queryset.filter(date__range=(start, end))
        elif params.get('archived', '').lower() == 'true':
            queryset = queryset.filter(date__lt=localdate())
        else:
            queryset = queryset.filter(date__gte=localdate())
        if params.get('filter') == 'today':
            queryset = queryset.filter(date=localdate())
        elif params.get('filter') == 'this_week':
            start = localdate() - timedelta(days=localdate().weekday())
            queryset = queryset.filter(date__range=(start, start + timedelta(days=6)))
        return queryset.order_by('date', 'time', 'pk')

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not user_is_admin(request.user):
            data.update(employee=request.user.pk, status='pending', requires_approval=True)
        lock_artists(data.get('employee'))
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        if self.request.user.role == "admin":
            appointment = serializer.save()
        else:
            appointment = serializer.save(
                employee=self.request.user,
                status="pending",
                requires_approval=True,
            )
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
    permission_classes = [IsOwnerOrAdmin]

    def update(self, request, *args, **kwargs):
        return Response(update_booking(request, kwargs['pk']))

    def get_queryset(self):
        if user_is_admin(self.request.user):
            return Appointment.objects.all()
        return Appointment.objects.filter(employee=self.request.user)

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
            "confirmed": queryset.filter(status="confirmed").count(),
            "completed": queryset.filter(status="completed").count(),
            "pending": queryset.filter(status="pending").count(),
            "canceled": queryset.filter(status="canceled").count(),
            "no_show": queryset.filter(status="no_show").count(),
        }

        return Response(data)

class AppointmentStatsView(APIView):
    """
    Returns appointment counts grouped by date for the last 30 days.
    Shape: [{ "date": "2025-01-01", "appointments": 5 }, ...]
    Consumed by the admin dashboard AppointmentsChart (line chart).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start = date.today() - timedelta(days=30)
        rows = (
            Appointment.objects.filter(date__gte=start)
            .values("date")
            .annotate(appointments=Count("id"))
            .order_by("date")
        )
        data = [
            {"date": row["date"].isoformat(), "appointments": row["appointments"]}
            for row in rows
        ]
        return Response(data)


class ArtistPerformanceView(APIView):
    """
    Returns appointment counts grouped by employee (artist).
    Shape: [{ "artist": "jane", "appointments": 20 }, ...]
    Consumed by the admin dashboard ArtistPerformanceChart (pie chart).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = (
            Appointment.objects.values("employee__username")
            .annotate(appointments=Count("id"))
            .order_by("-appointments")
        )
        data = [
            {"artist": row["employee__username"] or "Unassigned",
             "appointments": row["appointments"]}
            for row in rows
        ]
        return Response(data)


class RescheduleAppointmentView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        return Response(update_booking(request, pk))

# 🔹 Notification Views
class RecentActivityView(ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # A queue read must not delete pending requests or their rollback details.

        if user.role == "admin":
            # Exclude notifications where the employee is the current admin
            return Notifications.objects.exclude(employee=user).order_by("-timestamp")
        return Notifications.objects.filter(employee=user).order_by("-timestamp")


class ApproveNotificationView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        review_booking(request, pk, approve=True)
        return Response({'message': 'Appointment approved successfully.'})


class DeclineNotificationView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        review_booking(request, pk, approve=False)
        return Response({'message': 'Appointment request denied.'})


class DeleteNotificationView(APIView):
    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        notification = get_object_or_404(Notifications, pk=pk)
        if notification.status == 'pending':
            raise ValidationError({'error':'Approve or decline this request before removing its activity entry.'})
        notification.delete()
        return Response(status=204)

class KeyMetrics(APIView):
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]

    def post(self, request):
        data = request.data
        fee_type = data.get('fee_type')
        if fee_type not in ('flat', 'percentage'):
            raise ValidationError({'error':'Choose a flat or percentage studio fee.'})
        try:
            fee_value = Decimal(str(data.get('fee_value')))
        except Exception:
            raise ValidationError({'error':'Fee value must be numeric.'})
        if not fee_value.is_finite() or fee_value < 0:
            raise ValidationError({'error':'Enter a fee of zero or more.'})
        if fee_type == 'percentage' and fee_value > 100:
            raise ValidationError({'error':'The fee percentage must be between 0 and 100.'})
        try:
            if data.get('month') is not None or data.get('year') is not None:
                month, year = int(data.get('month')), int(data.get('year'))
                start = date(year, month, 1)
                end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
                end -= timedelta(days=1)
            elif data.get('start_date') or data.get('end_date'):
                start, end = date.fromisoformat(data.get('start_date')), date.fromisoformat(data.get('end_date'))
            else:
                end = localdate()
                start = end.replace(day=1)
        except (TypeError, ValueError, OverflowError):
            raise ValidationError({'error':'Choose a valid reporting period.'})
        if start > end:
            raise ValidationError({'error':'The start date must not be after the end date.'})

        # One read supplies both detail rows and totals. Round each session fee
        # to cents before summing so the visible rows reconcile with the report.
        appointments = list(Appointment.objects.filter(status='completed', date__range=(start, end))
                            .select_related('employee', 'client').order_by('date', 'pk'))
        grouped = {}
        for appointment in appointments:
            grouped.setdefault(appointment.employee_id, []).append(appointment)
        report = []
        shop_earnings = Decimal('0.00')
        for employee_id, bookings in grouped.items():
            rows = []
            for appointment in bookings:
                cut = fee_value if fee_type == 'flat' else appointment.price * fee_value / Decimal('100')
                cut = cut.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                rows.append({'client_name':str(appointment.client), 'date':appointment.date.isoformat(),
                             'price':float(appointment.price), 'shop_cut':float(cut),
                             'artist_cut':float(appointment.price - cut)})
            gross = sum((appointment.price for appointment in bookings), Decimal('0.00'))
            fee = sum((Decimal(str(row['shop_cut'])) for row in rows), Decimal('0.00'))
            shop_earnings += fee
            employee = bookings[0].employee
            report.append({'employee_id':employee_id,
                           'employee_name':employee.get_full_name() or employee.username,
                           'total_earned':float(gross), 'shop_fee':float(fee),
                           'net_payout':float(gross-fee), 'total_appointments':len(bookings),
                           'appointments':rows})
        return Response({'shop_total_revenue':float(sum((a.price for a in appointments), Decimal('0.00'))),
                         'shop_total_appointments':len(appointments),
                         'shop_total_earnings':float(shop_earnings), 'report':report})

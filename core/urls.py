from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from core.views import (
    RegisterView, LoginView, LogoutView, UserView,
    UserListView, UserDetailView,
    ClientProfileListView, ClientProfileDetailView,
    ServiceListView, ServiceDetailView,
    AppointmentListView, AppointmentDetailView, AppointmentOverviewView, RescheduleAppointmentView,
    RecentActivityView, ApproveNotificationView, DeclineNotificationView,
)

urlpatterns = [
    # Authentication
    path("api/register/", RegisterView.as_view(), name="register"),
    path("api/login/", LoginView.as_view(), name="login"),
    path("api/logout/", LogoutView.as_view(), name="logout"),
    path("api/user/", UserView.as_view(), name="user"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # User Management
    path("api/users/", UserListView.as_view(), name="user-list"),
    path("api/users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),

    # Client Profiles
    path("api/clients/", ClientProfileListView.as_view(), name="clientprofile-list"),
    path("api/clients/<int:pk>/", ClientProfileDetailView.as_view(), name="clientprofile-detail"),

    # Services
    path("api/services/", ServiceListView.as_view(), name="service-list"),
    path("api/services/<int:pk>/", ServiceDetailView.as_view(), name="service-detail"),

    # Appointments
    path("api/appointments/", AppointmentListView.as_view(), name="appointment-list"),
    path("api/appointments/<int:pk>/", AppointmentDetailView.as_view(), name="appointment-detail"),
    path("api/appointments/overview/", AppointmentOverviewView.as_view(), name="appointment-overview"),
    path("api/appointments/<int:pk>/reschedule/", RescheduleAppointmentView.as_view(), name="reschedule-appointment"),

    # Notifications
    path("api/recent-activity/", RecentActivityView.as_view(), name="recent-activity"),
    path("api/recent-activity/<int:pk>/approve/", ApproveNotificationView.as_view(), name="approve-notification"),
    path("api/recent-activity/<int:pk>/decline/", DeclineNotificationView.as_view(), name="decline-notification"),
]

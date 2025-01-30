from django.urls import path
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
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("user/", UserView.as_view(), name="user"),

    # User Management
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),

    # Client Profiles
    path("clients/", ClientProfileListView.as_view(), name="clientprofile-list"),
    path("clients/<int:pk>/", ClientProfileDetailView.as_view(), name="clientprofile-detail"),

    # Services
    path("services/", ServiceListView.as_view(), name="service-list"),
    path("services/<int:pk>/", ServiceDetailView.as_view(), name="service-detail"),

    # Appointments
    path("appointments/", AppointmentListView.as_view(), name="appointment-list"),
    path("appointments/<int:pk>/", AppointmentDetailView.as_view(), name="appointment-detail"),
    path("appointments/overview/", AppointmentOverviewView.as_view(), name="appointment-overview"),
    path("appointments/<int:pk>/reschedule/", RescheduleAppointmentView.as_view(), name="reschedule-appointment"),

    # Notifications
    path("recent-activity/", RecentActivityView.as_view(), name="recent-activity"),
    path("recent-activity/<int:pk>/approve/", ApproveNotificationView.as_view(), name="approve-notification"),
    path("recent-activity/<int:pk>/decline/", DeclineNotificationView.as_view(), name="decline-notification"),
]

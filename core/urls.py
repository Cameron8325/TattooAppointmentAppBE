from django.urls import path
from core.views import (
    UserListView,
    UserDetailView,
    ClientProfileListView,
    ClientProfileDetailView,
    ServiceListView,
    ServiceDetailView,
    AppointmentListView,
    AppointmentDetailView,
    RecentActivityView,
    ApproveNotificationView,
    DeclineNotificationView,
)

urlpatterns = [
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('clients/', ClientProfileListView.as_view(), name='clientprofile-list'),
    path('clients/<int:pk>/', ClientProfileDetailView.as_view(), name='clientprofile-detail'),
    path('services/', ServiceListView.as_view(), name='service-list'),
    path('services/<int:pk>/', ServiceDetailView.as_view(), name='service-detail'),
    path('appointments/', AppointmentListView.as_view(), name='appointment-list'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    path('recent-activity/', RecentActivityView.as_view(), name='recent-activity'),
    path('recent-activity/<int:pk>/approve/', ApproveNotificationView.as_view(), name='approve-notification'),
    path('recent-activity/<int:pk>/decline/', DeclineNotificationView.as_view(), name='decline-notification'),
]

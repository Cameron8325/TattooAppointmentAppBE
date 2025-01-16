from django.urls import path
from .views import ServiceListCreateView, ServiceDetailView, AppointmentListCreateView, AppointmentDetailView

urlpatterns = [
    path('services/', ServiceListCreateView.as_view(), name='service-list'),
    path('services/<int:pk>/', ServiceDetailView.as_view(), name='service-detail'),
    path('appointments/', AppointmentListCreateView.as_view(), name='appointment-list'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
]

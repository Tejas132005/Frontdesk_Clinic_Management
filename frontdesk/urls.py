from django.urls import path
from . import views

app_name = 'frontdesk'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),
    
    # Patient Management
    path('patients/', views.PatientListView.as_view(), name='patient_list'),
    path('patients/add/', views.PatientCreateView.as_view(), name='patient_add'),
    path('patients/<int:pk>/', views.patient_detail_view, name='patient_detail'),
    path('patients/<int:pk>/edit/', views.PatientUpdateView.as_view(), name='patient_edit'),
    path('patients/<int:pk>/delete/', views.PatientDeleteView.as_view(), name='patient_delete'),
    
    # Queue Management
    path('queue/', views.queue_management_view, name='queue_management'),
    path('queue/add/', views.add_to_queue_view, name='queue_add'),
    path('queue/<int:pk>/update-status/', views.update_queue_status_view, name='queue_update_status'),
    path('queue/<int:pk>/remove/', views.remove_from_queue_view, name='queue_remove'),
    path('queue/today/', views.today_queue_view, name='queue_today'),
    
    # Appointment Management
    path('appointments/', views.AppointmentListView.as_view(), name='appointment_list'),
    path('appointments/add/', views.AppointmentCreateView.as_view(), name='appointment_add'),
    path('appointments/<int:pk>/', views.appointment_detail_view, name='appointment_detail'),
    path('appointments/<int:pk>/edit/', views.AppointmentUpdateView.as_view(), name='appointment_edit'),
    path('appointments/<int:pk>/cancel/', views.cancel_appointment_view, name='appointment_cancel'),
    path('appointments/<int:pk>/reschedule/', views.reschedule_appointment_view, name='appointment_reschedule'),
    path('appointments/<int:pk>/confirm/', views.confirm_appointment_view, name='appointment_confirm'),
    path('appointments/<int:pk>/checkin/', views.checkin_appointment_view, name='appointment_checkin'),
    path('appointments/<int:pk>/complete/', views.complete_appointment_view, name='appointment_complete'),
    path('appointments/calendar/', views.appointment_calendar_view, name='appointment_calendar'),
    
    # Doctor Availability Management
    path('availability/', views.DoctorAvailabilityListView.as_view(), name='availability_list'),
    path('availability/add/', views.DoctorAvailabilityCreateView.as_view(), name='availability_add'),
    path('availability/<int:pk>/edit/', views.DoctorAvailabilityUpdateView.as_view(), name='availability_edit'),
    path('availability/<int:pk>/delete/', views.DoctorAvailabilityDeleteView.as_view(), name='availability_delete'),
    
    # AJAX endpoints
    path('api/patients/search/', views.search_patients_ajax, name='search_patients_ajax'),
    path('api/appointments/available-slots/', views.get_available_slots_ajax, name='available_slots_ajax'),
    path('api/queue/stats/', views.queue_stats_ajax, name='queue_stats_ajax'),
    path('api/dashboard/stats/', views.dashboard_stats_ajax, name='dashboard_stats_ajax'),
]
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.staff_login_view, name='login'),
    path('logout/', views.staff_logout_view, name='logout'),
    path('profile/', views.staff_profile_view, name='profile'),
    
    # Doctor Management
    path('doctors/', views.DoctorListView.as_view(), name='doctor_list'),
    path('doctors/add/', views.DoctorCreateView.as_view(), name='doctor_add'),
    path('doctors/<int:pk>/', views.doctor_detail_view, name='doctor_detail'),
    path('doctors/<int:pk>/edit/', views.DoctorUpdateView.as_view(), name='doctor_edit'),
    path('doctors/<int:pk>/delete/', views.DoctorDeleteView.as_view(), name='doctor_delete'),
    path('doctors/<int:pk>/toggle-availability/', views.toggle_doctor_availability, name='doctor_toggle_availability'),
    path('doctors/<int:pk>/quick-status/', views.quick_toggle_doctor_status, name='doctor_quick_status'),  # NEW
    
    # Doctor Schedule Management
    path('schedules/', views.DoctorScheduleListView.as_view(), name='schedule_list'),
    path('schedules/add/', views.DoctorScheduleCreateView.as_view(), name='schedule_add'),
    path('schedules/<int:pk>/edit/', views.DoctorScheduleUpdateView.as_view(), name='schedule_edit'),
    path('schedules/<int:pk>/delete/', views.DoctorScheduleDeleteView.as_view(), name='schedule_delete'),
    
    # AJAX endpoints
    path('api/doctors/search/', views.search_doctors_ajax, name='search_doctors_ajax'),
    path('api/doctors/by-specialization/', views.get_doctors_by_specialization, name='doctors_by_specialization'),
    path('api/doctors/<int:doctor_id>/availability/', views.get_doctor_availability, name='doctor_availability'),
]
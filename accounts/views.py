# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q

from .forms import (
    StaffLoginForm, StaffRegistrationForm, DoctorForm, 
    DoctorScheduleForm
)
from .models import CustomUser, FrontDeskStaff, Doctor, DoctorSchedule


# Helper function to check if user is staff
def is_staff_user(user):
    return user.is_authenticated and user.user_type == 'staff'


# Authentication Views
def staff_login_view(request):
    """
    Login view for front desk staff
    """
    if request.user.is_authenticated:
        return redirect('frontdesk:dashboard')
    
    if request.method == 'POST':
        form = StaffLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            
            # Redirect to next URL or dashboard
            next_url = request.GET.get('next', 'frontdesk:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = StaffLoginForm(request)
    
    context = {
        'form': form,
        'title': 'Staff Login'
    }
    return render(request, 'accounts/login.html', context)


@login_required
def staff_logout_view(request):
    """
    Logout view
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
@user_passes_test(is_staff_user)
def staff_profile_view(request):
    """
    Staff profile view
    """
    staff_profile = get_object_or_404(FrontDeskStaff, user=request.user)
    
    context = {
        'staff_profile': staff_profile,
        'title': 'My Profile'
    }
    return render(request, 'accounts/profile.html', context)


# Doctor Management Views
class DoctorListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    List all doctors
    """
    model = Doctor
    template_name = 'accounts/doctor_list.html'
    context_object_name = 'doctors'
    paginate_by = 20
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def get_queryset(self):
        queryset = Doctor.objects.all().order_by('full_name')
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) |
                Q(doctor_id__icontains=search_query) |
                Q(specialization__icontains=search_query)
            )
        
        # Filter by specialization
        specialization = self.request.GET.get('specialization', '')
        if specialization:
            queryset = queryset.filter(specialization__icontains=specialization)
        
        # Filter by location
        location = self.request.GET.get('location', '')
        if location:
            queryset = queryset.filter(clinic_location__icontains=location)
        
        # Filter by availability
        availability = self.request.GET.get('availability', '')
        if availability == 'available':
            queryset = queryset.filter(is_available=True)
        elif availability == 'unavailable':
            queryset = queryset.filter(is_available=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Doctors'
        context['search_query'] = self.request.GET.get('search', '')
        context['specializations'] = Doctor.objects.values_list(
            'specialization', flat=True
        ).distinct()
        return context


class DoctorCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create new doctor profile
    """
    model = Doctor
    form_class = DoctorForm
    template_name = 'accounts/doctor_form.html'
    success_url = reverse_lazy('accounts:doctor_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f'Doctor {form.instance.full_name} added successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Doctor'
        context['button_text'] = 'Add Doctor'
        return context


class DoctorUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update doctor profile
    """
    model = Doctor
    form_class = DoctorForm
    template_name = 'accounts/doctor_form.html'
    success_url = reverse_lazy('accounts:doctor_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f'Doctor {form.instance.full_name} updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Doctor - {self.object.full_name}'
        context['button_text'] = 'Update Doctor'
        return context


class DoctorDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete doctor profile
    """
    model = Doctor
    template_name = 'accounts/doctor_confirm_delete.html'
    success_url = reverse_lazy('accounts:doctor_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        doctor = self.get_object()
        messages.success(request, f'Doctor {doctor.full_name} deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
@user_passes_test(is_staff_user)
def doctor_detail_view(request, pk):
    """
    View doctor details with schedule
    """
    doctor = get_object_or_404(Doctor, pk=pk)
    schedules = DoctorSchedule.objects.filter(doctor=doctor, is_active=True)
    
    context = {
        'doctor': doctor,
        'schedules': schedules,
        'title': f'Dr. {doctor.full_name}'
    }
    return render(request, 'accounts/doctor_detail.html', context)


# Doctor Schedule Management
class DoctorScheduleListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    List all doctor schedules
    """
    model = DoctorSchedule
    template_name = 'accounts/schedule_list.html'
    context_object_name = 'schedules'
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def get_queryset(self):
        queryset = DoctorSchedule.objects.select_related('doctor').all()
        
        # Filter by doctor if provided
        doctor_id = self.request.GET.get('doctor', '')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        
        return queryset.order_by('doctor__full_name', 'day_of_week', 'start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Doctor Schedules'
        context['doctors'] = Doctor.objects.all()
        return context


class DoctorScheduleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create new schedule for a doctor
    """
    model = DoctorSchedule
    form_class = DoctorScheduleForm
    template_name = 'accounts/schedule_form.html'
    success_url = reverse_lazy('accounts:schedule_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Schedule added successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Doctor Schedule'
        context['button_text'] = 'Add Schedule'
        return context


class DoctorScheduleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update doctor schedule
    """
    model = DoctorSchedule
    form_class = DoctorScheduleForm
    template_name = 'accounts/schedule_form.html'
    success_url = reverse_lazy('accounts:schedule_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Schedule updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Schedule'
        context['button_text'] = 'Update Schedule'
        return context


class DoctorScheduleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete doctor schedule
    """
    model = DoctorSchedule
    template_name = 'accounts/schedule_confirm_delete.html'
    success_url = reverse_lazy('accounts:schedule_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Schedule deleted successfully!')
        return super().delete(request, *args, **kwargs)


# AJAX Views for dynamic data
@login_required
@user_passes_test(is_staff_user)
def get_doctors_by_specialization(request):
    """
    API endpoint to get doctors filtered by specialization
    """
    specialization = request.GET.get('specialization', '')
    doctors = Doctor.objects.filter(
        specialization__icontains=specialization,
        is_available=True
    ).values('id', 'full_name', 'doctor_id')
    
    return JsonResponse(list(doctors), safe=False)


@login_required
@user_passes_test(is_staff_user)
def get_doctor_availability(request, doctor_id):
    """
    Get doctor's availability for a specific date
    """
    from datetime import datetime
    from frontdesk.models import DoctorAvailability
    
    date_str = request.GET.get('date', '')
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    doctor = get_object_or_404(Doctor, id=doctor_id)
    availability = DoctorAvailability.objects.filter(
        doctor=doctor,
        date=date,
        is_available=True
    ).first()
    
    if availability:
        slots = availability.get_available_time_slots()
        return JsonResponse({
            'available': True,
            'slots': [{
                'time': slot['time'].strftime('%H:%M'),
                'available': slot['available']
            } for slot in slots]
        })
    else:
        return JsonResponse({'available': False, 'slots': []})


@login_required
@user_passes_test(is_staff_user)
def toggle_doctor_availability(request, pk):
    """
    Toggle doctor's availability status
    """
    doctor = get_object_or_404(Doctor, pk=pk)
    doctor.is_available = not doctor.is_available
    doctor.save()
    
    status = 'available' if doctor.is_available else 'unavailable'
    messages.success(request, f'Dr. {doctor.full_name} is now {status}.')
    
    return redirect('accounts:doctor_list')


# Search doctors view
@login_required
@user_passes_test(is_staff_user)
def search_doctors_ajax(request):
    """
    AJAX search for doctors
    """
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    doctors = Doctor.objects.filter(
        Q(full_name__icontains=query) |
        Q(doctor_id__icontains=query) |
        Q(specialization__icontains=query)
    )[:10]
    
    results = [{
        'id': doctor.id,
        'doctor_id': doctor.doctor_id,
        'name': doctor.full_name,
        'specialization': doctor.specialization,
        'is_available': doctor.is_available
    } for doctor in doctors]
    
    return JsonResponse(results, safe=False)


@login_required
@user_passes_test(is_staff_user)
def quick_toggle_doctor_status(request, pk):
    """
    Quick toggle doctor availability status via AJAX
    """
    if request.method == 'POST':
        doctor = get_object_or_404(Doctor, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status == 'available':
            doctor.is_available = True
            doctor.save()
            message = f'Dr. {doctor.full_name} is now Available'
            status = 'success'
        elif new_status == 'busy':
            doctor.is_available = False
            doctor.save()
            message = f'Dr. {doctor.full_name} is now Busy'
            status = 'warning'
        elif new_status == 'off_duty':
            doctor.is_available = False
            doctor.save()
            message = f'Dr. {doctor.full_name} is now Off Duty'
            status = 'danger'
        else:
            message = 'Invalid status'
            status = 'error'
        
        # Get next availability
        from datetime import datetime, date
        from frontdesk.models import DoctorAvailability
        
        next_availability = DoctorAvailability.objects.filter(
            doctor=doctor,
            date__gte=date.today(),
            is_available=True
        ).order_by('date', 'start_time').first()
        
        next_available_text = 'Not scheduled'
        if next_availability:
            next_available_text = f"{next_availability.date.strftime('%b %d')} at {next_availability.start_time.strftime('%I:%M %p')}"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'status': status,
                'next_available': next_available_text
            })
        else:
            messages.success(request, message)
            return redirect('accounts:doctor_list')
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
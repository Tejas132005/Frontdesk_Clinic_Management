# frontdesk/views.py

from .models import Patient, Queue, Appointment, DoctorAvailability
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import date, datetime, timedelta
from accounts.models import Doctor, FrontDeskStaff
from .forms import (
    PatientForm, QueueForm, QueueStatusUpdateForm, AppointmentForm,
    AppointmentRescheduleForm, AppointmentCancelForm, DoctorAvailabilityForm,
    QuickPatientSearchForm, DateRangeFilterForm
)


# Helper function to check if user is staff
def is_staff_user(user):
    return user.is_authenticated and user.user_type == 'staff'


# Dashboard View
@login_required
@user_passes_test(is_staff_user)
def dashboard_view(request):
    """
    Main dashboard for front desk staff
    """
    today = date.today()
    
    # Get today's statistics
    today_appointments = Appointment.objects.filter(appointment_date=today)
    today_queue = Queue.objects.filter(queue_date=today)
    
    stats = {
        'total_appointments_today': today_appointments.count(),
        'pending_appointments': today_appointments.filter(
            status__in=['scheduled', 'confirmed']
        ).count(),
        'completed_appointments': today_appointments.filter(status='completed').count(),
        'total_in_queue': today_queue.filter(status='waiting').count(),
        'patients_with_doctor': today_queue.filter(status='with_doctor').count(),
        'total_patients': Patient.objects.filter(is_active=True).count(),
        'available_doctors': Doctor.objects.filter(is_available=True).count(),
    }
    
    # Recent appointments
    recent_appointments = Appointment.objects.select_related(
        'patient', 'doctor'
    ).filter(
        appointment_date=today
    ).order_by('appointment_time')[:5]
    
    # Current queue
    current_queue = Queue.objects.select_related(
        'patient', 'doctor'
    ).filter(
        queue_date=today,
        status__in=['waiting', 'with_doctor']
    ).order_by('priority', 'arrival_time')[:10]
    
    # Upcoming appointments (next 3 days)
    upcoming_appointments = Appointment.objects.select_related(
        'patient', 'doctor'
    ).filter(
        appointment_date__range=[today, today + timedelta(days=3)],
        status__in=['scheduled', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')[:10]
    
    context = {
        'title': 'Dashboard',
        'stats': stats,
        'recent_appointments': recent_appointments,
        'current_queue': current_queue,
        'upcoming_appointments': upcoming_appointments,
    }
    
    return render(request, 'frontdesk/dashboard.html', context)


# Patient Management Views
class PatientListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    List all patients
    """
    model = Patient
    template_name = 'frontdesk/patient_list.html'
    context_object_name = 'patients'
    paginate_by = 20
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def get_queryset(self):
        queryset = Patient.objects.filter(is_active=True).order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(patient_id__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(phone_number__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Patients'
        context['search_form'] = QuickPatientSearchForm(self.request.GET)
        return context


class PatientCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Add new patient
    """
    model = Patient
    form_class = PatientForm
    template_name = 'frontdesk/patient_form.html'
    success_url = reverse_lazy('frontdesk:patient_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def form_valid(self, form):
        patient = form.save(commit=False)
        try:
            staff_profile = FrontDeskStaff.objects.get(user=self.request.user)
            patient.registered_by = staff_profile
        except FrontDeskStaff.DoesNotExist:
            pass
        
        patient.save()
        messages.success(
            self.request,
            f'Patient {patient.get_full_name()} (ID: {patient.patient_id}) registered successfully!'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Register New Patient'
        context['button_text'] = 'Register Patient'
        return context


class PatientUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update patient information
    """
    model = Patient
    form_class = PatientForm
    template_name = 'frontdesk/patient_form.html'
    success_url = reverse_lazy('frontdesk:patient_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f'Patient {form.instance.get_full_name()} updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Patient - {self.object.get_full_name()}'
        context['button_text'] = 'Update Patient'
        return context


class PatientDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Soft delete patient (set is_active to False)
    """
    model = Patient
    template_name = 'frontdesk/patient_confirm_delete.html'
    success_url = reverse_lazy('frontdesk:patient_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        messages.success(request, f'Patient {self.object.get_full_name()} deactivated successfully!')
        return redirect(self.success_url)


@login_required
@user_passes_test(is_staff_user)
def patient_detail_view(request, pk):
    """
    View patient details with appointments and queue history
    """
    patient = get_object_or_404(Patient, pk=pk)
    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date')[:10]
    queue_history = Queue.objects.filter(patient=patient).order_by('-queue_date')[:10]
    
    context = {
        'title': f'Patient - {patient.get_full_name()}',
        'patient': patient,
        'appointments': appointments,
        'queue_history': queue_history,
    }
    
    return render(request, 'frontdesk/patient_detail.html', context)


# Queue Management Views
@login_required
@user_passes_test(is_staff_user)
def queue_management_view(request):
    """
    Queue management page
    """
    today = date.today()
    queue_entries = Queue.objects.filter(
        queue_date=today
    ).select_related('patient', 'doctor').order_by('priority', 'arrival_time')
    
    # Queue statistics
    stats = {
        'waiting': queue_entries.filter(status='waiting').count(),
        'with_doctor': queue_entries.filter(status='with_doctor').count(),
        'completed': queue_entries.filter(status='completed').count(),
        'total': queue_entries.count(),
    }
    
    context = {
        'title': 'Queue Management',
        'queue_entries': queue_entries,
        'stats': stats,
        'available_doctors': Doctor.objects.filter(is_available=True, accepts_walkins=True),
    }
    
    return render(request, 'frontdesk/queue_management.html', context)


@login_required
@user_passes_test(is_staff_user)
def add_to_queue_view(request):
    """
    Add patient to queue
    """
    if request.method == 'POST':
        form = QueueForm(request.POST)
        if form.is_valid():
            try:
                staff_profile = FrontDeskStaff.objects.get(user=request.user)
                queue_entry = form.save(commit=False, added_by=staff_profile)
                queue_entry.save()
                
                messages.success(
                    request,
                    f'Patient {queue_entry.patient.get_full_name()} added to queue. '
                    f'Queue number: {queue_entry.queue_number}'
                )
                return redirect('frontdesk:queue_management')
            except FrontDeskStaff.DoesNotExist:
                messages.error(request, 'Staff profile not found.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QueueForm()
    
    context = {
        'title': 'Add to Queue',
        'form': form,
    }
    
    return render(request, 'frontdesk/queue_add.html', context)


@login_required
@user_passes_test(is_staff_user)
def update_queue_status_view(request, pk):
    """
    Update queue entry status
    """
    queue_entry = get_object_or_404(Queue, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        if new_status in dict(Queue.STATUS_CHOICES):
            old_status = queue_entry.status
            queue_entry.status = new_status
            
            # Update timestamps based on status
            if new_status == 'with_doctor':
                queue_entry.mark_with_doctor()
                # Mark doctor as busy
                if queue_entry.doctor:
                    queue_entry.doctor.is_available = False
                    queue_entry.doctor.save()
                    messages.info(request, f'Dr. {queue_entry.doctor.full_name} is now marked as Busy')
                    
            elif new_status == 'completed':
                queue_entry.mark_completed()
                # Mark doctor as available again
                if queue_entry.doctor:
                    queue_entry.doctor.is_available = True
                    queue_entry.doctor.save()
                    messages.success(request, f'Dr. {queue_entry.doctor.full_name} is now Available')
            else:
                queue_entry.save()
            
            messages.success(request, f'Queue status updated to {queue_entry.get_status_display()}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('frontdesk:queue_management')


@login_required
@user_passes_test(is_staff_user)
def remove_from_queue_view(request, pk):
    """
    Remove/cancel queue entry
    """
    queue_entry = get_object_or_404(Queue, pk=pk)
    
    if request.method == 'POST':
        queue_entry.status = 'cancelled'
        queue_entry.save()
        messages.success(request, f'Queue entry #{queue_entry.queue_number} cancelled.')
    
    return redirect('frontdesk:queue_management')


@login_required
@user_passes_test(is_staff_user)
def today_queue_view(request):
    """
    View today's queue (AJAX-friendly)
    """
    today = date.today()
    queue_entries = Queue.objects.filter(
        queue_date=today,
        status__in=['waiting', 'with_doctor']
    ).select_related('patient', 'doctor').order_by('priority', 'arrival_time')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = [{
            'id': q.id,
            'queue_number': q.queue_number,
            'patient_name': q.patient.get_full_name(),
            'doctor_name': q.doctor.full_name if q.doctor else 'Not Assigned',
            'status': q.get_status_display(),
            'priority': q.get_priority_display(),
            'wait_time': q.get_wait_time(),
        } for q in queue_entries]
        return JsonResponse(data, safe=False)
    
    return redirect('frontdesk:queue_management')


# Appointment Management Views
class AppointmentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    List all appointments
    """
    model = Appointment
    template_name = 'frontdesk/appointment_list.html'
    context_object_name = 'appointments'
    paginate_by = 20
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def get_queryset(self):
        queryset = Appointment.objects.select_related(
            'patient', 'doctor'
        ).all().order_by('-appointment_date', '-appointment_time')
        
        # Filter by status
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by date range
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
        
        if start_date:
            queryset = queryset.filter(appointment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(appointment_date__lte=end_date)
        
        # Filter by doctor
        doctor_id = self.request.GET.get('doctor', '')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        
        # Search
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(appointment_id__icontains=search_query) |
                Q(patient__first_name__icontains=search_query) |
                Q(patient__last_name__icontains=search_query) |
                Q(patient__patient_id__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Appointments'
        context['doctors'] = Doctor.objects.all()
        context['status_choices'] = Appointment.STATUS_CHOICES
        context['date_range_form'] = DateRangeFilterForm(self.request.GET)
        return context


class AppointmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Schedule new appointment
    """
    model = Appointment
    form_class = AppointmentForm
    template_name = 'frontdesk/appointment_form.html'
    success_url = reverse_lazy('frontdesk:appointment_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def form_valid(self, form):
        try:
            staff_profile = FrontDeskStaff.objects.get(user=self.request.user)
            appointment = form.save(commit=False)
            
            # Generate appointment ID before saving
            if not appointment.appointment_id:
                appointment.appointment_id = Appointment.generate_appointment_id()
            
            appointment.scheduled_by = staff_profile
            appointment.save()
            
            messages.success(
                self.request,
                f'Appointment scheduled successfully! Appointment ID: {appointment.appointment_id}'
            )
            return redirect(self.success_url)
        except FrontDeskStaff.DoesNotExist:
            messages.error(self.request, 'Staff profile not found.')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Error creating appointment: {str(e)}')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Schedule New Appointment'
        context['button_text'] = 'Schedule Appointment'
        return context


class AppointmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update appointment details
    """
    model = Appointment
    form_class = AppointmentForm
    template_name = 'frontdesk/appointment_form.html'
    success_url = reverse_lazy('frontdesk:appointment_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Disable certain fields if appointment cannot be modified
        if self.object.status in ['completed', 'cancelled']:
            for field in form.fields:
                form.fields[field].disabled = True
        return form
    
    def form_valid(self, form):
        if self.object.status in ['completed', 'cancelled']:
            messages.error(self.request, 'Cannot modify completed or cancelled appointments.')
            return redirect(self.success_url)
        
        messages.success(self.request, 'Appointment updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Appointment - {self.object.appointment_id}'
        context['button_text'] = 'Update Appointment'
        return context


@login_required
@user_passes_test(is_staff_user)
def appointment_detail_view(request, pk):
    """
    View appointment details
    """
    appointment = get_object_or_404(Appointment.objects.select_related('patient', 'doctor'), pk=pk)
    
    context = {
        'title': f'Appointment - {appointment.appointment_id}',
        'appointment': appointment,
    }
    
    return render(request, 'frontdesk/appointment_detail.html', context)


@login_required
@user_passes_test(is_staff_user)
def cancel_appointment_view(request, pk):
    """
    Cancel an appointment
    """
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if not appointment.can_cancel():
        messages.error(request, 'This appointment cannot be cancelled.')
        return redirect('frontdesk:appointment_detail', pk=pk)
    
    if request.method == 'POST':
        form = AppointmentCancelForm(request.POST)
        if form.is_valid():
            try:
                staff_profile = FrontDeskStaff.objects.get(user=request.user)
                appointment.cancel_appointment(
                    reason=form.cleaned_data['cancellation_reason'],
                    cancelled_by=staff_profile
                )
                messages.success(request, f'Appointment {appointment.appointment_id} cancelled successfully.')
                return redirect('frontdesk:appointment_list')
            except FrontDeskStaff.DoesNotExist:
                messages.error(request, 'Staff profile not found.')
    else:
        form = AppointmentCancelForm()
    
    context = {
        'title': f'Cancel Appointment - {appointment.appointment_id}',
        'appointment': appointment,
        'form': form,
    }
    
    return render(request, 'frontdesk/appointment_cancel.html', context)


@login_required
@user_passes_test(is_staff_user)
def reschedule_appointment_view(request, pk):
    """
    Reschedule an appointment
    """
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if not appointment.can_reschedule():
        messages.error(request, 'This appointment cannot be rescheduled.')
        return redirect('frontdesk:appointment_detail', pk=pk)
    
    if request.method == 'POST':
        form = AppointmentRescheduleForm(request.POST, appointment=appointment)
        if form.is_valid():
            # Create new appointment
            new_appointment = Appointment.objects.create(
                patient=appointment.patient,
                doctor=appointment.doctor,
                appointment_date=form.cleaned_data['new_date'],
                appointment_time=form.cleaned_data['new_time'],
                duration=appointment.duration,
                appointment_type=appointment.appointment_type,
                reason_for_visit=appointment.reason_for_visit,
                symptoms=appointment.symptoms,
                special_instructions=appointment.special_instructions,
                scheduled_by=appointment.scheduled_by,
                rescheduled_from=appointment
            )
            new_appointment.appointment_id = Appointment.generate_appointment_id()
            new_appointment.save()
            
            # Mark old appointment as rescheduled
            appointment.status = 'rescheduled'
            appointment.notes = f"Rescheduled to {new_appointment.appointment_date} {new_appointment.appointment_time}. Reason: {form.cleaned_data.get('reason', 'Not specified')}"
            appointment.save()
            
            messages.success(
                request,
                f'Appointment rescheduled successfully! New appointment ID: {new_appointment.appointment_id}'
            )
            return redirect('frontdesk:appointment_detail', pk=new_appointment.pk)
    else:
        form = AppointmentRescheduleForm(appointment=appointment)
    
    context = {
        'title': f'Reschedule Appointment - {appointment.appointment_id}',
        'appointment': appointment,
        'form': form,
    }
    
    return render(request, 'frontdesk/appointment_reschedule.html', context)


@login_required
@user_passes_test(is_staff_user)
def confirm_appointment_view(request, pk):
    """
    Confirm an appointment
    """
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if appointment.status == 'scheduled':
        appointment.mark_confirmed()
        messages.success(request, f'Appointment {appointment.appointment_id} confirmed.')
    else:
        messages.warning(request, 'Appointment is already confirmed or cannot be confirmed.')
    
    return redirect('frontdesk:appointment_detail', pk=pk)


@login_required
@user_passes_test(is_staff_user)
def checkin_appointment_view(request, pk):
    """
    Check-in patient for appointment
    """
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if appointment.status in ['scheduled', 'confirmed']:
        appointment.mark_checked_in()
        messages.success(request, f'Patient {appointment.patient.get_full_name()} checked in.')
    else:
        messages.warning(request, 'Cannot check in this appointment.')
    
    return redirect('frontdesk:appointment_detail', pk=pk)


@login_required
@user_passes_test(is_staff_user)
def complete_appointment_view(request, pk):
    """
    Mark appointment as completed
    """
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if appointment.status in ['checked_in', 'in_progress']:
        appointment.complete_appointment()
        messages.success(request, f'Appointment {appointment.appointment_id} marked as completed.')
    else:
        messages.warning(request, 'Cannot complete this appointment.')
    
    return redirect('frontdesk:appointment_detail', pk=pk)


@login_required
@user_passes_test(is_staff_user)
def appointment_calendar_view(request):
    """
    Calendar view of appointments
    """
    # Get month and year from query params or use current
    month = int(request.GET.get('month', datetime.now().month))
    year = int(request.GET.get('year', datetime.now().year))
    
    # Get all appointments for the month
    appointments = Appointment.objects.filter(
        appointment_date__year=year,
        appointment_date__month=month
    ).select_related('patient', 'doctor')
    
    context = {
        'title': 'Appointment Calendar',
        'appointments': appointments,
        'current_month': month,
        'current_year': year,
    }
    
    return render(request, 'frontdesk/appointment_calendar.html', context)


# Doctor Availability Management
class DoctorAvailabilityListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    List doctor availability
    """
    model = DoctorAvailability
    template_name = 'frontdesk/availability_list.html'
    context_object_name = 'availabilities'
    paginate_by = 20
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def get_queryset(self):
        queryset = DoctorAvailability.objects.select_related('doctor').filter(
            date__gte=date.today()
        ).order_by('date', 'start_time')
        
        # Filter by doctor
        doctor_id = self.request.GET.get('doctor', '')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Doctor Availability'
        context['doctors'] = Doctor.objects.all()
        return context


class DoctorAvailabilityCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create doctor availability slot
    """
    model = DoctorAvailability
    form_class = DoctorAvailabilityForm
    template_name = 'frontdesk/availability_form.html'
    success_url = reverse_lazy('frontdesk:availability_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Doctor availability added successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Doctor Availability'
        context['button_text'] = 'Add Availability'
        return context


class DoctorAvailabilityUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update doctor availability
    """
    model = DoctorAvailability
    form_class = DoctorAvailabilityForm
    template_name = 'frontdesk/availability_form.html'
    success_url = reverse_lazy('frontdesk:availability_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Doctor availability updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Doctor Availability'
        context['button_text'] = 'Update Availability'
        return context


class DoctorAvailabilityDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete doctor availability
    """
    model = DoctorAvailability
    template_name = 'frontdesk/availability_confirm_delete.html'
    success_url = reverse_lazy('frontdesk:availability_list')
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Doctor availability deleted successfully!')
        return super().delete(request, *args, **kwargs)


# AJAX Views
@login_required
@user_passes_test(is_staff_user)
def search_patients_ajax(request):
    """
    AJAX search for patients
    """
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    patients = Patient.objects.filter(
        Q(patient_id__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(phone_number__icontains=query),
        is_active=True
    )[:10]
    
    results = [{
        'id': patient.id,
        'patient_id': patient.patient_id,
        'name': patient.get_full_name(),
        'phone': patient.phone_number,
        'age': patient.get_age(),
    } for patient in patients]
    
    return JsonResponse(results, safe=False)


@login_required
@user_passes_test(is_staff_user)
def get_available_slots_ajax(request):
    """
    Get available time slots for a doctor on a specific date
    """
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')
    
    if not doctor_id or not date_str:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        doctor = Doctor.objects.get(id=doctor_id)
    except (ValueError, Doctor.DoesNotExist):
        return JsonResponse({'error': 'Invalid doctor or date'}, status=400)
    
    # Get doctor availability for the date
    availability = DoctorAvailability.objects.filter(
        doctor=doctor,
        date=appointment_date,
        is_available=True
    ).first()
    
    if not availability:
        return JsonResponse({'available': False, 'slots': []})
    
    slots = availability.get_available_time_slots()
    
    return JsonResponse({
        'available': True,
        'slots': [{
            'time': slot['time'].strftime('%H:%M'),
            'available': slot['available']
        } for slot in slots]
    })


@login_required
@user_passes_test(is_staff_user)
def queue_stats_ajax(request):
    """
    Get real-time queue statistics
    """
    today = date.today()
    queue_entries = Queue.objects.filter(queue_date=today)
    
    stats = {
        'waiting': queue_entries.filter(status='waiting').count(),
        'with_doctor': queue_entries.filter(status='with_doctor').count(),
        'completed': queue_entries.filter(status='completed').count(),
        'cancelled': queue_entries.filter(status='cancelled').count(),
        'total': queue_entries.count(),
        'avg_wait_time': 0,
    }
    
    # Calculate average wait time
    completed_entries = queue_entries.filter(status='completed')
    if completed_entries.exists():
        total_wait = sum([entry.get_wait_time() for entry in completed_entries])
        stats['avg_wait_time'] = round(total_wait / completed_entries.count(), 2)
    
    return JsonResponse(stats)


@login_required
@user_passes_test(is_staff_user)
def dashboard_stats_ajax(request):
    """
    Get dashboard statistics (for real-time updates)
    """
    today = date.today()
    
    appointments_today = Appointment.objects.filter(appointment_date=today)
    queue_today = Queue.objects.filter(queue_date=today)
    
    stats = {
        'appointments': {
            'total': appointments_today.count(),
            'scheduled': appointments_today.filter(status='scheduled').count(),
            'confirmed': appointments_today.filter(status='confirmed').count(),
            'checked_in': appointments_today.filter(status='checked_in').count(),
            'completed': appointments_today.filter(status='completed').count(),
            'cancelled': appointments_today.filter(status='cancelled').count(),
        },
        'queue': {
            'waiting': queue_today.filter(status='waiting').count(),
            'with_doctor': queue_today.filter(status='with_doctor').count(),
            'completed': queue_today.filter(status='completed').count(),
        },
        'doctors': {
            'available': Doctor.objects.filter(is_available=True).count(),
            'total': Doctor.objects.count(),
        },
        'patients': {
            'total': Patient.objects.filter(is_active=True).count(),
        }
    }
    
    return JsonResponse(stats)
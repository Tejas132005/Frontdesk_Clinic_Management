from django import forms
from django.core.exceptions import ValidationError
from datetime import date, datetime, timedelta
from .models import Patient, Queue, Appointment, DoctorAvailability
from accounts.models import Doctor


class PatientForm(forms.ModelForm):
    """
    Form for adding/editing patient information
    """
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'max': date.today().isoformat()
        })
    )
    
    class Meta:
        model = Patient
        fields = [
            'patient_id', 'first_name', 'last_name', 'date_of_birth', 'gender',
            'blood_group', 'phone_number', 'email', 'address_line1', 'address_line2',
            'city', 'state', 'pincode', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relation',
            'allergies', 'chronic_conditions', 'current_medications'
        ]
        widgets = {
            'patient_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-generated if left empty'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street Address'
            }),
            'address_line2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apartment, Suite, etc.'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State'
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pincode'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency Contact Name'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency Contact Phone'
            }),
            'emergency_contact_relation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Relation (e.g., Spouse, Parent)'
            }),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List any known allergies'
            }),
            'chronic_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List any chronic conditions'
            }),
            'current_medications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List current medications'
            }),
        }
    
    def clean_patient_id(self):
        patient_id = self.cleaned_data.get('patient_id')
        if not patient_id:
            # Auto-generate patient ID
            last_patient = Patient.objects.all().order_by('-id').first()
            if last_patient:
                last_id = int(last_patient.patient_id.replace('PAT', ''))
                patient_id = f"PAT{last_id + 1:05d}"
            else:
                patient_id = "PAT00001"
        return patient_id
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > date.today():
            raise ValidationError("Date of birth cannot be in the future.")
        return dob


class QueueForm(forms.ModelForm):
    """
    Form for adding patients to the queue
    """
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'patient-select'
        }),
        empty_label="Select Patient"
    )
    
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.filter(is_available=True, accepts_walkins=True),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=False,
        empty_label="Select Doctor (Optional)"
    )
    
    class Meta:
        model = Queue
        fields = ['patient', 'doctor', 'priority', 'reason_for_visit', 'notes']
        widgets = {
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reason_for_visit': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Brief description of reason for visit'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes (optional)'
            }),
        }
    
    def save(self, commit=True, added_by=None):
        queue_entry = super().save(commit=False)
        queue_entry.queue_number = Queue.generate_queue_number()
        queue_entry.queue_date = date.today()
        
        if added_by:
            queue_entry.added_by = added_by
        
        # Calculate estimated wait time based on current queue
        if queue_entry.doctor:
            waiting_count = Queue.objects.filter(
                doctor=queue_entry.doctor,
                status='waiting',
                queue_date=date.today()
            ).count()
            queue_entry.estimated_wait_time = waiting_count * 15  # 15 minutes per patient
        
        if commit:
            queue_entry.save()
        
        return queue_entry


class QueueStatusUpdateForm(forms.ModelForm):
    """
    Form for updating queue status
    """
    class Meta:
        model = Queue
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }


class AppointmentForm(forms.ModelForm):
    """
    Form for scheduling appointments
    """
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'appointment-patient-select'
        }),
        empty_label="Select Patient"
    )
    
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.filter(is_available=True),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'appointment-doctor-select'
        }),
        empty_label="Select Doctor"
    )
    
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': date.today().isoformat()
        })
    )
    
    appointment_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    
    class Meta:
        model = Appointment
        fields = [
            'patient', 'doctor', 'appointment_date', 'appointment_time',
            'duration', 'appointment_type', 'reason_for_visit',
            'symptoms', 'special_instructions'
        ]
        widgets = {
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 15,
                'step': 15,
                'value': 30
            }),
            'appointment_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reason_for_visit': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Reason for visit'
            }),
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Current symptoms (optional)'
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any special instructions (optional)'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        doctor = cleaned_data.get('doctor')
        
        if appointment_date and appointment_time and doctor:
            # Check if appointment is in the past
            from django.utils import timezone
            appointment_datetime = datetime.combine(appointment_date, appointment_time)
            if timezone.is_naive(appointment_datetime):
                appointment_datetime = timezone.make_aware(appointment_datetime)
            
            if appointment_datetime < timezone.now():
                raise ValidationError("Cannot schedule appointments in the past.")
            
            # Check if doctor is available at this time
            existing_appointment = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=['scheduled', 'confirmed', 'checked_in']
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if existing_appointment.exists():
                raise ValidationError(
                    f"Dr. {doctor.full_name} already has an appointment at this time."
                )
        
        return cleaned_data
    
    def save(self, commit=True, scheduled_by=None):
        appointment = super().save(commit=False)
        
        # Don't set appointment_id here - let the view handle it
        if scheduled_by:
            appointment.scheduled_by = scheduled_by
        
        if commit:
            # Generate ID if not set
            if not appointment.appointment_id:
                appointment.appointment_id = Appointment.generate_appointment_id()
            appointment.save()
        
        return appointment


class AppointmentRescheduleForm(forms.Form):
    """
    Form for rescheduling appointments
    """
    new_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': date.today().isoformat()
        }),
        label='New Appointment Date'
    )
    
    new_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        label='New Appointment Time'
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Reason for rescheduling'
        }),
        required=False,
        label='Reason for Rescheduling'
    )
    
    def __init__(self, *args, appointment=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.appointment = appointment
    
    def clean(self):
        cleaned_data = super().clean()
        new_date = cleaned_data.get('new_date')
        new_time = cleaned_data.get('new_time')
        
        if new_date and new_time and self.appointment:
            # Check if new time is in the past
            new_datetime = datetime.combine(new_date, new_time)
            if new_datetime < datetime.now():
                raise ValidationError("Cannot reschedule to a time in the past.")
            
            # Check if doctor is available at new time
            existing = Appointment.objects.filter(
                doctor=self.appointment.doctor,
                appointment_date=new_date,
                appointment_time=new_time,
                status__in=['scheduled', 'confirmed', 'checked_in']
            ).exclude(pk=self.appointment.pk)
            
            if existing.exists():
                raise ValidationError(
                    "Doctor already has an appointment at this time. Please choose another slot."
                )
        
        return cleaned_data


class AppointmentCancelForm(forms.Form):
    """
    Form for canceling appointments
    """
    cancellation_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Please provide a reason for cancellation'
        }),
        label='Reason for Cancellation',
        required=True
    )


class DoctorAvailabilityForm(forms.ModelForm):
    """
    Form for managing doctor availability
    """
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': date.today().isoformat()
        })
    )
    
    class Meta:
        model = DoctorAvailability
        fields = [
            'doctor', 'date', 'start_time', 'end_time',
            'is_available', 'max_appointments', 'unavailability_reason'
        ]
        widgets = {
            'doctor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'max_appointments': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'unavailability_reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Emergency, Leave, Conference'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError("End time must be after start time.")
        
        return cleaned_data


class QuickPatientSearchForm(forms.Form):
    """
    Quick search form for finding patients
    """
    search_query = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, ID, or phone number',
            'id': 'patient-search-input'
        }),
        required=False,
        label=''
    )


class DateRangeFilterForm(forms.Form):
    """
    Form for filtering by date range
    """
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False,
        label='From Date'
    )
    
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False,
        label='To Date'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError("End date must be after start date.")
        
        return cleaned_data
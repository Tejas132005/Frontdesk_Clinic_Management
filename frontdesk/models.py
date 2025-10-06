# frontdesk/models.py

from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from accounts.models import Doctor, FrontDeskStaff
from datetime import date, datetime, timedelta


class Patient(models.Model):
    """
    Patient model to store patient information
    """
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )
    
    # Basic Information
    patient_id = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Unique patient identifier"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(
        max_length=3, 
        choices=BLOOD_GROUP_CHOICES,
        blank=True,
        null=True
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17)
    email = models.EmailField(blank=True, null=True)
    
    # Address
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(
        validators=[phone_regex], 
        max_length=17,
        blank=True
    )
    emergency_contact_relation = models.CharField(max_length=50, blank=True)
    
    # Medical Information
    allergies = models.TextField(
        blank=True,
        help_text="List any known allergies"
    )
    chronic_conditions = models.TextField(
        blank=True,
        help_text="List any chronic medical conditions"
    )
    current_medications = models.TextField(
        blank=True,
        help_text="List current medications"
    )
    
    # Registration Info
    registered_by = models.ForeignKey(
        FrontDeskStaff,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_patients'
    )
    registration_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patient'
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['last_name', 'first_name']),
        ]
    
    def __str__(self):
        return f"{self.patient_id} - {self.get_full_name()}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def get_full_address(self):
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.pincode
        ]
        return ', '.join(filter(None, parts))


class Queue(models.Model):
    """
    Queue management for walk-in patients
    """
    STATUS_CHOICES = (
        ('waiting', 'Waiting'),
        ('with_doctor', 'With Doctor'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )
    
    PRIORITY_CHOICES = (
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    )
    
    # Queue Information
    queue_number = models.CharField(max_length=10, unique=True)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='queue_entries'
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='queue_entries',
        null=True,
        blank=True
    )
    
    # Queue Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='waiting'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal'
    )
    
    # Timestamps
    arrival_time = models.DateTimeField(auto_now_add=True)
    called_time = models.DateTimeField(null=True, blank=True)
    consultation_start_time = models.DateTimeField(null=True, blank=True)
    consultation_end_time = models.DateTimeField(null=True, blank=True)
    
    # Estimated wait time in minutes
    estimated_wait_time = models.IntegerField(
        default=0,
        help_text="Estimated wait time in minutes"
    )
    
    # Reason for visit
    reason_for_visit = models.TextField(blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Staff who added to queue
    added_by = models.ForeignKey(
        FrontDeskStaff,
        on_delete=models.SET_NULL,
        null=True,
        related_name='queue_entries_added'
    )
    
    # Date of queue entry (for filtering by date)
    queue_date = models.DateField(default=date.today)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'queue'
        verbose_name = 'Queue Entry'
        verbose_name_plural = 'Queue Entries'
        ordering = ['priority', 'arrival_time']
        indexes = [
            models.Index(fields=['queue_date', 'status']),
            models.Index(fields=['doctor', 'status']),
        ]
    
    def __str__(self):
        return f"Queue #{self.queue_number} - {self.patient.get_full_name()} ({self.get_status_display()})"
    
    def get_wait_time(self):
        """Calculate actual wait time"""
        if self.consultation_start_time:
            wait_time = self.consultation_start_time - self.arrival_time
            return int(wait_time.total_seconds() / 60)
        elif self.status == 'waiting':
            wait_time = timezone.now() - self.arrival_time
            return int(wait_time.total_seconds() / 60)
        return 0
    
    def mark_with_doctor(self):
        """Mark patient as with doctor"""
        self.status = 'with_doctor'
        self.consultation_start_time = timezone.now()
        self.save()
    
    def mark_completed(self):
        """Mark queue entry as completed"""
        self.status = 'completed'
        self.consultation_end_time = timezone.now()
        self.save()
    
    @staticmethod
    def generate_queue_number():
        """Generate unique queue number for today"""
        today = date.today()
        today_queues = Queue.objects.filter(queue_date=today).count()
        return f"Q{today.strftime('%Y%m%d')}{today_queues + 1:03d}"


class Appointment(models.Model):
    """
    Appointment scheduling model
    """
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    )
    
    APPOINTMENT_TYPE_CHOICES = (
        ('new', 'New Patient'),
        ('follow_up', 'Follow Up'),
        ('routine', 'Routine Checkup'),
        ('emergency', 'Emergency'),
    )
    
    # Appointment Information
    appointment_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique appointment identifier"
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    
    # Scheduling
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    duration = models.IntegerField(
        default=30,
        help_text="Appointment duration in minutes"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    appointment_type = models.CharField(
        max_length=20,
        choices=APPOINTMENT_TYPE_CHOICES,
        default='routine'
    )
    
    # Details
    reason_for_visit = models.TextField()
    symptoms = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Scheduling metadata
    scheduled_by = models.ForeignKey(
        FrontDeskStaff,
        on_delete=models.SET_NULL,
        null=True,
        related_name='appointments_scheduled'
    )
    scheduled_at = models.DateTimeField(auto_now_add=True)
    
    # Confirmation
    is_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Check-in
    checked_in_at = models.DateTimeField(null=True, blank=True)
    
    # Consultation times
    consultation_start_time = models.DateTimeField(null=True, blank=True)
    consultation_end_time = models.DateTimeField(null=True, blank=True)
    
    # Cancellation/Rescheduling
    cancellation_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        FrontDeskStaff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments_cancelled'
    )
    
    # Rescheduling
    rescheduled_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rescheduled_to'
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Reminder sent
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'appointment'
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        ordering = ['appointment_date', 'appointment_time']
        unique_together = ['doctor', 'appointment_date', 'appointment_time']
        indexes = [
            models.Index(fields=['appointment_date', 'status']),
            models.Index(fields=['patient', 'appointment_date']),
            models.Index(fields=['doctor', 'appointment_date']),
        ]
    
    def __str__(self):
        return f"{self.appointment_id} - {self.patient.get_full_name()} with Dr. {self.doctor.full_name} on {self.appointment_date}"
    
    def get_end_time(self):
        """Calculate appointment end time"""
        dt = datetime.combine(date.today(), self.appointment_time)
        end_dt = dt + timedelta(minutes=self.duration)
        return end_dt.time()
    
    def is_past(self):
        """Check if appointment is in the past"""
        from django.utils import timezone
        
        appointment_datetime = datetime.combine(
            self.appointment_date, 
            self.appointment_time
        )
        
        # Make the datetime timezone-aware
        if timezone.is_naive(appointment_datetime):
            appointment_datetime = timezone.make_aware(appointment_datetime)
        
        return appointment_datetime < timezone.now()
    
    def can_cancel(self):
        """Check if appointment can be cancelled"""
        return self.status in ['scheduled', 'confirmed'] and not self.is_past()
    
    def can_reschedule(self):
        """Check if appointment can be rescheduled"""
        return self.status in ['scheduled', 'confirmed'] and not self.is_past()
    
    def mark_confirmed(self):
        """Confirm the appointment"""
        self.status = 'confirmed'
        self.is_confirmed = True
        self.confirmed_at = timezone.now()
        self.save()
    
    def mark_checked_in(self):
        """Mark patient as checked in"""
        self.status = 'checked_in'
        self.checked_in_at = timezone.now()
        self.save()
    
    def start_consultation(self):
        """Start the consultation"""
        self.status = 'in_progress'
        self.consultation_start_time = timezone.now()
        self.save()
    
    def complete_appointment(self):
        """Complete the appointment"""
        self.status = 'completed'
        self.consultation_end_time = timezone.now()
        self.save()
    
    def cancel_appointment(self, reason, cancelled_by=None):
        """Cancel the appointment"""
        self.status = 'cancelled'
        self.cancellation_reason = reason
        self.cancelled_at = timezone.now()
        self.cancelled_by = cancelled_by
        self.save()
    
    @staticmethod
    def generate_appointment_id():
        """Generate unique appointment ID"""
        import random
        import string
        
        today = date.today()
        date_str = today.strftime('%Y%m%d')
        
        # Try to generate a unique ID with incrementing counter
        max_attempts = 100
        for attempt in range(max_attempts):
            # Count appointments created today
            today_count = Appointment.objects.filter(
                appointment_id__startswith=f"APT{date_str}"
            ).count()
            
            # Generate ID with counter
            appointment_id = f"APT{date_str}{today_count + 1:04d}"
            
            # Check if this ID already exists
            if not Appointment.objects.filter(appointment_id=appointment_id).exists():
                return appointment_id
        
        # Fallback: add random suffix if we somehow still have collision
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"APT{date_str}{random_suffix}"


class DoctorAvailability(models.Model):
    """
    Daily availability slots for doctors
    """
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='availability_slots'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    is_available = models.BooleanField(default=True)
    max_appointments = models.IntegerField(
        default=10,
        help_text="Maximum appointments for this slot"
    )
    
    # Reason for unavailability
    unavailability_reason = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g., Emergency, Leave, Conference"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'doctor_availability'
        verbose_name = 'Doctor Availability'
        verbose_name_plural = 'Doctor Availabilities'
        unique_together = ['doctor', 'date', 'start_time']
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['doctor', 'date']),
            models.Index(fields=['date', 'is_available']),
        ]
    
    def __str__(self):
        return f"Dr. {self.doctor.full_name} - {self.date} ({self.start_time}-{self.end_time})"
    
    def get_booked_slots(self):
        """Get count of booked appointments for this slot"""
        return Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.date,
            appointment_time__gte=self.start_time,
            appointment_time__lt=self.end_time,
            status__in=['scheduled', 'confirmed', 'checked_in']
        ).count()
    
    def has_available_slots(self):
        """Check if slot has availability"""
        if not self.is_available:
            return False
        return self.get_booked_slots() < self.max_appointments
    
    def get_available_time_slots(self, slot_duration=30):
        """Generate available time slots"""
        from datetime import datetime, timedelta
        
        slots = []
        current_time = datetime.combine(date.today(), self.start_time)
        end_time = datetime.combine(date.today(), self.end_time)
        
        while current_time < end_time:
            # Check if this specific time slot is available
            slot_time = current_time.time()
            is_booked = Appointment.objects.filter(
                doctor=self.doctor,
                appointment_date=self.date,
                appointment_time=slot_time,
                status__in=['scheduled', 'confirmed', 'checked_in']
            ).exists()
            
            slots.append({
                'time': slot_time,
                'available': not is_booked
            })
            
            current_time += timedelta(minutes=slot_duration)
        
        return slots
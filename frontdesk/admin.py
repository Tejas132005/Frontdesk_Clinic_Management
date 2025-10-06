from django.contrib import admin
from .models import Patient, Queue, Appointment, DoctorAvailability


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'get_full_name', 'phone_number', 'gender', 
                    'get_age', 'registration_date', 'is_active']
    list_filter = ['gender', 'blood_group', 'is_active', 'registration_date']
    search_fields = ['patient_id', 'first_name', 'last_name', 'phone_number', 'email']
    readonly_fields = ['created_at', 'updated_at', 'registration_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient_id', 'first_name', 'last_name', 'date_of_birth', 
                      'gender', 'blood_group')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'pincode')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 
                      'emergency_contact_relation'),
            'classes': ('collapse',)
        }),
        ('Medical Information', {
            'fields': ('allergies', 'chronic_conditions', 'current_medications'),
            'classes': ('collapse',)
        }),
        ('Registration', {
            'fields': ('registered_by', 'registration_date', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    list_display = ['queue_number', 'patient', 'doctor', 'status', 'priority', 
                    'arrival_time', 'get_wait_time']
    list_filter = ['status', 'priority', 'queue_date', 'doctor']
    search_fields = ['queue_number', 'patient__first_name', 'patient__last_name']
    readonly_fields = ['arrival_time', 'created_at', 'updated_at']
    date_hierarchy = 'queue_date'
    
    fieldsets = (
        ('Queue Information', {
            'fields': ('queue_number', 'patient', 'doctor', 'queue_date')
        }),
        ('Status', {
            'fields': ('status', 'priority', 'reason_for_visit')
        }),
        ('Timestamps', {
            'fields': ('arrival_time', 'called_time', 'consultation_start_time', 
                      'consultation_end_time', 'estimated_wait_time')
        }),
        ('Additional Information', {
            'fields': ('notes', 'added_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['appointment_id', 'patient', 'doctor', 'appointment_date', 
                    'appointment_time', 'status', 'is_confirmed']
    list_filter = ['status', 'appointment_type', 'appointment_date', 'is_confirmed']
    search_fields = ['appointment_id', 'patient__first_name', 'patient__last_name', 
                    'doctor__full_name']
    readonly_fields = ['scheduled_at', 'created_at', 'updated_at']
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('Appointment Information', {
            'fields': ('appointment_id', 'patient', 'doctor', 'appointment_date', 
                      'appointment_time', 'duration')
        }),
        ('Status', {
            'fields': ('status', 'appointment_type', 'is_confirmed', 'confirmed_at')
        }),
        ('Details', {
            'fields': ('reason_for_visit', 'symptoms', 'special_instructions')
        }),
        ('Check-in & Consultation', {
            'fields': ('checked_in_at', 'consultation_start_time', 'consultation_end_time'),
            'classes': ('collapse',)
        }),
        ('Cancellation/Rescheduling', {
            'fields': ('cancellation_reason', 'cancelled_at', 'cancelled_by', 
                      'rescheduled_from'),
            'classes': ('collapse',)
        }),
        ('Scheduling Info', {
            'fields': ('scheduled_by', 'scheduled_at', 'reminder_sent', 
                      'reminder_sent_at', 'notes'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'start_time', 'end_time', 'is_available', 
                    'get_booked_slots', 'max_appointments']
    list_filter = ['is_available', 'date', 'doctor']
    search_fields = ['doctor__full_name']
    date_hierarchy = 'date'
    
    def get_booked_slots(self, obj):
        return f"{obj.get_booked_slots()}/{obj.max_appointments}"
    get_booked_slots.short_description = 'Booked/Max'
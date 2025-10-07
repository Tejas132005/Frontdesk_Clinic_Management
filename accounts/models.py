# accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser
    """
    USER_TYPE_CHOICES = (
        ('staff', 'Front Desk Staff'),
        ('doctor', 'Doctor'),
    )
    
    user_type = models.CharField(
        max_length=10, 
        choices=USER_TYPE_CHOICES,
        default='staff'
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        blank=True,
        null=True
    )
    is_active_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'custom_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class FrontDeskStaff(models.Model):
    """
    Profile model for Front Desk Staff
    """
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='staff_profile',
        limit_choices_to={'user_type': 'staff'}
    )
    employee_id = models.CharField(max_length=20, unique=True)
    shift = models.CharField(
        max_length=20,
        choices=(
            ('morning', 'Morning (6 AM - 2 PM)'),
            ('afternoon', 'Afternoon (2 PM - 10 PM)'),
            ('night', 'Night (10 PM - 6 AM)'),
        ),
        default='morning'
    )
    department = models.CharField(max_length=100, default='Reception')
    date_joined = models.DateField(auto_now_add=True)
    
    class Meta:
        db_table = 'frontdesk_staff'
        verbose_name = 'Front Desk Staff'
        verbose_name_plural = 'Front Desk Staff'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id}"


class Doctor(models.Model):
    """
    Doctor profile model with specialization and availability
    """
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        limit_choices_to={'user_type': 'doctor'},
        null=True,
        blank=True
    )
    doctor_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    specialization = models.CharField(
        max_length=100,
        help_text="e.g., General Practice, Pediatrics, Cardiology, Dermatology"
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=17)
    email = models.EmailField()
    
    # Location and availability
    clinic_location = models.CharField(
        max_length=200,
        help_text="Clinic or hospital location"
    )
    consultation_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    
    # Availability flags
    is_available = models.BooleanField(
        default=True,
        help_text="Is the doctor currently available for appointments?"
    )
    accepts_walkins = models.BooleanField(
        default=True,
        help_text="Does the doctor accept walk-in patients?"
    )
    
    # Professional details
    license_number = models.CharField(max_length=50, unique=True)
    years_of_experience = models.IntegerField(default=0)
    qualifications = models.TextField(
        blank=True,
        help_text="Medical degrees and certifications"
    )
    bio = models.TextField(blank=True)
    
    # Timestamps
    date_joined = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'doctor'
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['specialization']),
            models.Index(fields=['clinic_location']),
            models.Index(fields=['is_available']),
        ]

    def __str__(self):
        return f"Dr. {self.full_name} - {self.specialization}"

    def get_current_availability_status(self):
        """Returns current availability status as a string"""
        if not self.is_available:
            return "Off Duty"
        
        # Check if doctor has any available slots today
        from datetime import date
        from frontdesk.models import DoctorAvailability
        
        today_availability = DoctorAvailability.objects.filter(
            doctor=self,
            date=date.today(),
            is_available=True
        ).first()
        
        if today_availability:
            return "Available"
        return "Busy"


class DoctorSchedule(models.Model):
    """
    Weekly schedule for doctors
    """
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='weekly_schedule'
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.IntegerField(
        default=30,
        help_text="Duration of each appointment slot in minutes"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'doctor_schedule'
        verbose_name = 'Doctor Schedule'
        verbose_name_plural = 'Doctor Schedules'
        unique_together = ['doctor', 'day_of_week', 'start_time']
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.doctor.full_name} - {self.get_day_of_week_display()} ({self.start_time}-{self.end_time})"
    
    
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create FrontDeskStaff or Doctor profile when a user is created
    """
    if created:
        if instance.user_type == 'staff':
            # Check if profile doesn't already exist
            if not FrontDeskStaff.objects.filter(user=instance).exists():
                # Generate employee_id
                staff_count = FrontDeskStaff.objects.count()
                employee_id = f'EMP{staff_count + 1:04d}'
                
                FrontDeskStaff.objects.create(
                    user=instance,
                    employee_id=employee_id,
                    shift='morning',
                    department='Reception'
                )
                print(f"✅ Created FrontDeskStaff profile for {instance.username}")

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """
    Ensure profile exists even if created manually through admin
    This handles cases where user_type is changed after creation
    """
    if instance.user_type == 'staff':
        if not FrontDeskStaff.objects.filter(user=instance).exists():
            staff_count = FrontDeskStaff.objects.count()
            employee_id = f'EMP{staff_count + 1:04d}'
            
            FrontDeskStaff.objects.create(
                user=instance,
                employee_id=employee_id,
                shift='morning',
                department='Reception'
            )
            print(f"✅ Auto-created missing FrontDeskStaff profile for {instance.username}")
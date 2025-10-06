from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, FrontDeskStaff, Doctor, DoctorSchedule


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'user_type', 'is_active_user', 'date_joined']
    list_filter = ['user_type', 'is_active_user', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'is_active_user')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number')}),
    )


@admin.register(FrontDeskStaff)
class FrontDeskStaffAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'get_full_name', 'shift', 'department', 'date_joined']
    list_filter = ['shift', 'department']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'


class DoctorScheduleInline(admin.TabularInline):
    model = DoctorSchedule
    extra = 1


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['doctor_id', 'full_name', 'specialization', 'clinic_location', 
                    'is_available', 'phone_number']
    list_filter = ['specialization', 'clinic_location', 'is_available', 'gender']
    search_fields = ['doctor_id', 'full_name', 'specialization', 'email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [DoctorScheduleInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'doctor_id', 'full_name', 'gender', 'specialization')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'clinic_location')
        }),
        ('Professional Details', {
            'fields': ('license_number', 'years_of_experience', 'qualifications', 'bio')
        }),
        ('Availability & Pricing', {
            'fields': ('is_available', 'accepts_walkins', 'consultation_fee')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'day_of_week', 'start_time', 'end_time', 'slot_duration', 'is_active']
    list_filter = ['day_of_week', 'is_active']
    search_fields = ['doctor__full_name']
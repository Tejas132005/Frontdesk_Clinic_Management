# accounts/management/commands/setup_initial_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import CustomUser, FrontDeskStaff, Doctor, DoctorSchedule
from frontdesk.models import Patient, DoctorAvailability
from datetime import date, time, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up initial data for Allo Health system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before setting up new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        self.stdout.write('Setting up initial data...')
        
        # Create superuser if it doesn't exist
        self.create_superuser()
        
        # Create front desk staff
        self.create_frontdesk_staff()
        
        # Create doctors
        self.create_doctors()
        
        # Create patients
        self.create_patients()
        
        # Create doctor schedules
        self.create_doctor_schedules()
        
        # Create doctor availability
        self.create_doctor_availability()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up initial data!')
        )

    def clear_data(self):
        """Clear existing data"""
        DoctorAvailability.objects.all().delete()
        DoctorSchedule.objects.all().delete()
        Patient.objects.all().delete()
        Doctor.objects.all().delete()
        FrontDeskStaff.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    def create_superuser(self):
        """Create superuser if it doesn't exist"""
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@allohealth.com',
                password='admin123',
                first_name='System',
                last_name='Administrator'
            )
            self.stdout.write('Created superuser: admin/admin123')

    def create_frontdesk_staff(self):
        """Create front desk staff users"""
        staff_data = [
            {
                'username': 'reception1',
                'email': 'reception1@allohealth.com',
                'password': 'staff123',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'employee_id': 'EMP001',
                'shift': 'morning',
                'department': 'Reception'
            },
            {
                'username': 'reception2',
                'email': 'reception2@allohealth.com',
                'password': 'staff123',
                'first_name': 'Michael',
                'last_name': 'Chen',
                'employee_id': 'EMP002',
                'shift': 'afternoon',
                'department': 'Reception'
            },
            {
                'username': 'reception3',
                'email': 'reception3@allohealth.com',
                'password': 'staff123',
                'first_name': 'Emily',
                'last_name': 'Davis',
                'employee_id': 'EMP003',
                'shift': 'night',
                'department': 'Reception'
            }
        ]

        for data in staff_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'user_type': 'staff',
                    'is_staff': True,
                    'is_active': True
                }
            )
            
            if created:
                user.set_password(data['password'])
                user.save()
                
                FrontDeskStaff.objects.create(
                    user=user,
                    employee_id=data['employee_id'],
                    shift=data['shift'],
                    department=data['department']
                )
                self.stdout.write(f'Created staff: {data["username"]}/staff123')

    def create_doctors(self):
        """Create doctor users and profiles"""
        doctors_data = [
            {
                'username': 'dr_smith',
                'email': 'dr.smith@allohealth.com',
                'password': 'doctor123',
                'first_name': 'John',
                'last_name': 'Smith',
                'doctor_id': 'DOC001',
                'full_name': 'Dr. John Smith',
                'specialization': 'General Practice',
                'gender': 'M',
                'phone_number': '+1234567890',
                'clinic_location': 'Main Clinic - Floor 1',
                'consultation_fee': 150.00,
                'license_number': 'MD123456',
                'years_of_experience': 15,
                'qualifications': 'MD, Internal Medicine',
                'bio': 'Experienced general practitioner with expertise in preventive care and chronic disease management.'
            },
            {
                'username': 'dr_johnson',
                'email': 'dr.johnson@allohealth.com',
                'password': 'doctor123',
                'first_name': 'Lisa',
                'last_name': 'Johnson',
                'doctor_id': 'DOC002',
                'full_name': 'Dr. Lisa Johnson',
                'specialization': 'Pediatrics',
                'gender': 'F',
                'phone_number': '+1234567891',
                'clinic_location': 'Pediatric Wing - Floor 2',
                'consultation_fee': 175.00,
                'license_number': 'MD123457',
                'years_of_experience': 12,
                'qualifications': 'MD, Pediatrics, Child Development Specialist',
                'bio': 'Pediatrician specializing in child health and development with a gentle approach to patient care.'
            },
            {
                'username': 'dr_williams',
                'email': 'dr.williams@allohealth.com',
                'password': 'doctor123',
                'first_name': 'Robert',
                'last_name': 'Williams',
                'doctor_id': 'DOC003',
                'full_name': 'Dr. Robert Williams',
                'specialization': 'Cardiology',
                'gender': 'M',
                'phone_number': '+1234567892',
                'clinic_location': 'Cardiology Center - Floor 3',
                'consultation_fee': 250.00,
                'license_number': 'MD123458',
                'years_of_experience': 20,
                'qualifications': 'MD, Cardiology, Interventional Cardiology',
                'bio': 'Cardiologist with extensive experience in heart disease diagnosis and treatment.'
            },
            {
                'username': 'dr_brown',
                'email': 'dr.brown@allohealth.com',
                'password': 'doctor123',
                'first_name': 'Maria',
                'last_name': 'Brown',
                'doctor_id': 'DOC004',
                'full_name': 'Dr. Maria Brown',
                'specialization': 'Dermatology',
                'gender': 'F',
                'phone_number': '+1234567893',
                'clinic_location': 'Dermatology Clinic - Floor 2',
                'consultation_fee': 200.00,
                'license_number': 'MD123459',
                'years_of_experience': 10,
                'qualifications': 'MD, Dermatology, Cosmetic Dermatology',
                'bio': 'Dermatologist specializing in skin health, cosmetic procedures, and dermatological conditions.'
            },
            {
                'username': 'dr_davis',
                'email': 'dr.davis@allohealth.com',
                'password': 'doctor123',
                'first_name': 'David',
                'last_name': 'Davis',
                'doctor_id': 'DOC005',
                'full_name': 'Dr. David Davis',
                'specialization': 'Orthopedics',
                'gender': 'M',
                'phone_number': '+1234567894',
                'clinic_location': 'Orthopedic Center - Floor 4',
                'consultation_fee': 225.00,
                'license_number': 'MD123460',
                'years_of_experience': 18,
                'qualifications': 'MD, Orthopedic Surgery, Sports Medicine',
                'bio': 'Orthopedic surgeon specializing in joint replacement and sports medicine.'
            }
        ]

        for data in doctors_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'user_type': 'doctor',
                    'is_staff': True,
                    'is_active': True
                }
            )
            
            if created:
                user.set_password(data['password'])
                user.save()
                
                Doctor.objects.create(
                    user=user,
                    doctor_id=data['doctor_id'],
                    full_name=data['full_name'],
                    specialization=data['specialization'],
                    gender=data['gender'],
                    phone_number=data['phone_number'],
                    email=data['email'],
                    clinic_location=data['clinic_location'],
                    consultation_fee=data['consultation_fee'],
                    license_number=data['license_number'],
                    years_of_experience=data['years_of_experience'],
                    qualifications=data['qualifications'],
                    bio=data['bio']
                )
                self.stdout.write(f'Created doctor: {data["username"]}/doctor123')

    def create_patients(self):
        """Create sample patients"""
        patients_data = [
            {
                'patient_id': 'PAT001',
                'first_name': 'Alice',
                'last_name': 'Wilson',
                'date_of_birth': date(1985, 3, 15),
                'gender': 'F',
                'blood_group': 'A+',
                'phone_number': '+1987654321',
                'email': 'alice.wilson@email.com',
                'address_line1': '123 Main Street',
                'city': 'New York',
                'state': 'NY',
                'pincode': '10001',
                'emergency_contact_name': 'Bob Wilson',
                'emergency_contact_phone': '+1987654322',
                'emergency_contact_relation': 'Spouse',
                'allergies': 'Penicillin',
                'chronic_conditions': 'Hypertension'
            },
            {
                'patient_id': 'PAT002',
                'first_name': 'James',
                'last_name': 'Miller',
                'date_of_birth': date(1990, 7, 22),
                'gender': 'M',
                'blood_group': 'O+',
                'phone_number': '+1987654323',
                'email': 'james.miller@email.com',
                'address_line1': '456 Oak Avenue',
                'city': 'Los Angeles',
                'state': 'CA',
                'pincode': '90210',
                'emergency_contact_name': 'Sarah Miller',
                'emergency_contact_phone': '+1987654324',
                'emergency_contact_relation': 'Sister',
                'allergies': 'None',
                'chronic_conditions': 'Diabetes Type 2'
            },
            {
                'patient_id': 'PAT003',
                'first_name': 'Emma',
                'last_name': 'Garcia',
                'date_of_birth': date(1978, 11, 8),
                'gender': 'F',
                'blood_group': 'B+',
                'phone_number': '+1987654325',
                'email': 'emma.garcia@email.com',
                'address_line1': '789 Pine Street',
                'city': 'Chicago',
                'state': 'IL',
                'pincode': '60601',
                'emergency_contact_name': 'Carlos Garcia',
                'emergency_contact_phone': '+1987654326',
                'emergency_contact_relation': 'Brother',
                'allergies': 'Shellfish',
                'chronic_conditions': 'Asthma'
            },
            {
                'patient_id': 'PAT004',
                'first_name': 'Michael',
                'last_name': 'Taylor',
                'date_of_birth': date(1995, 5, 30),
                'gender': 'M',
                'blood_group': 'AB+',
                'phone_number': '+1987654327',
                'email': 'michael.taylor@email.com',
                'address_line1': '321 Elm Drive',
                'city': 'Houston',
                'state': 'TX',
                'pincode': '77001',
                'emergency_contact_name': 'Jennifer Taylor',
                'emergency_contact_phone': '+1987654328',
                'emergency_contact_relation': 'Mother',
                'allergies': 'None',
                'chronic_conditions': 'None'
            },
            {
                'patient_id': 'PAT005',
                'first_name': 'Sophia',
                'last_name': 'Anderson',
                'date_of_birth': date(1982, 9, 12),
                'gender': 'F',
                'blood_group': 'A-',
                'phone_number': '+1987654329',
                'email': 'sophia.anderson@email.com',
                'address_line1': '654 Maple Lane',
                'city': 'Phoenix',
                'state': 'AZ',
                'pincode': '85001',
                'emergency_contact_name': 'Thomas Anderson',
                'emergency_contact_phone': '+1987654330',
                'emergency_contact_relation': 'Father',
                'allergies': 'Latex',
                'chronic_conditions': 'Arthritis'
            }
        ]

        # Get a front desk staff member to assign as registered_by
        staff = FrontDeskStaff.objects.first()
        
        for data in patients_data:
            patient, created = Patient.objects.get_or_create(
                patient_id=data['patient_id'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'date_of_birth': data['date_of_birth'],
                    'gender': data['gender'],
                    'blood_group': data['blood_group'],
                    'phone_number': data['phone_number'],
                    'email': data['email'],
                    'address_line1': data['address_line1'],
                    'city': data['city'],
                    'state': data['state'],
                    'pincode': data['pincode'],
                    'emergency_contact_name': data['emergency_contact_name'],
                    'emergency_contact_phone': data['emergency_contact_phone'],
                    'emergency_contact_relation': data['emergency_contact_relation'],
                    'allergies': data['allergies'],
                    'chronic_conditions': data['chronic_conditions'],
                    'registered_by': staff
                }
            )
            
            if created:
                self.stdout.write(f'Created patient: {data["patient_id"]} - {data["first_name"]} {data["last_name"]}')

    def create_doctor_schedules(self):
        """Create weekly schedules for doctors"""
        doctors = Doctor.objects.all()
        
        for doctor in doctors:
            # Create schedule for Monday to Friday
            for day in range(0, 5):  # Monday to Friday
                DoctorSchedule.objects.get_or_create(
                    doctor=doctor,
                    day_of_week=day,
                    defaults={
                        'start_time': time(9, 0),  # 9:00 AM
                        'end_time': time(17, 0),   # 5:00 PM
                        'slot_duration': 30,
                        'is_active': True
                    }
                )
            
            # Create Saturday schedule (half day)
            DoctorSchedule.objects.get_or_create(
                doctor=doctor,
                day_of_week=5,  # Saturday
                defaults={
                    'start_time': time(9, 0),  # 9:00 AM
                    'end_time': time(13, 0),   # 1:00 PM
                    'slot_duration': 30,
                    'is_active': True
                }
            )
        
        self.stdout.write('Created doctor schedules')

    def create_doctor_availability(self):
        """Create availability slots for the next 30 days"""
        doctors = Doctor.objects.all()
        today = date.today()
        
        for doctor in doctors:
            for i in range(30):  # Next 30 days
                current_date = today + timedelta(days=i)
                
                # Skip Sundays
                if current_date.weekday() == 6:
                    continue
                
                # Create morning slot
                DoctorAvailability.objects.get_or_create(
                    doctor=doctor,
                    date=current_date,
                    start_time=time(9, 0),
                    end_time=time(12, 0),
                    defaults={
                        'is_available': True,
                        'max_appointments': 6
                    }
                )
                
                # Create afternoon slot
                DoctorAvailability.objects.get_or_create(
                    doctor=doctor,
                    date=current_date,
                    start_time=time(14, 0),
                    end_time=time(17, 0),
                    defaults={
                        'is_available': True,
                        'max_appointments': 6
                    }
                )
        
        self.stdout.write('Created doctor availability slots')

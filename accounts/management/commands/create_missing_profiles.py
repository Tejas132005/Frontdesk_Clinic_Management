from django.core.management.base import BaseCommand
from accounts.models import CustomUser, FrontDeskStaff, Doctor

class Command(BaseCommand):
    help = 'Create missing FrontDeskStaff profiles for existing staff users'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Checking for users without profiles...'))
        
        # Fix staff users
        staff_users = CustomUser.objects.filter(user_type='staff')
        staff_fixed = 0
        
        for user in staff_users:
            if not FrontDeskStaff.objects.filter(user=user).exists():
                staff_count = FrontDeskStaff.objects.count()
                employee_id = f'EMP{staff_count + 1:04d}'
                
                FrontDeskStaff.objects.create(
                    user=user,
                    employee_id=employee_id,
                    shift='morning',
                    department='Reception'
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created profile for staff user: {user.username} ({employee_id})')
                )
                staff_fixed += 1
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {user.username} already has profile')
                )
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n=== Summary ==='))
        self.stdout.write(self.style.SUCCESS(f'Staff profiles created: {staff_fixed}'))
        self.stdout.write(self.style.SUCCESS(f'Total staff users: {staff_users.count()}'))
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import CustomUser, FrontDeskStaff, Doctor, DoctorSchedule


class StaffLoginForm(AuthenticationForm):
    """
    Custom login form for front desk staff
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Invalid username or password.",
                    code='invalid_login'
                )
            
            # Check if user is staff
            if self.user_cache.user_type != 'staff':
                raise forms.ValidationError(
                    "This account does not have staff access.",
                    code='invalid_user_type'
                )
            
            if not self.user_cache.is_active_user:
                raise forms.ValidationError(
                    "This account has been deactivated.",
                    code='inactive'
                )
        
        return self.cleaned_data


class StaffRegistrationForm(UserCreationForm):
    """
    Form for registering new front desk staff
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Staff specific fields
    employee_id = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    shift = forms.ChoiceField(
        choices=FrontDeskStaff._meta.get_field('shift').choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    department = forms.CharField(
        required=False,
        initial='Reception',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 
                 'phone_number', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'staff'
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Create FrontDeskStaff profile
            FrontDeskStaff.objects.create(
                user=user,
                employee_id=self.cleaned_data['employee_id'],
                shift=self.cleaned_data['shift'],
                department=self.cleaned_data.get('department', 'Reception')
            )
        
        return user


class DoctorForm(forms.ModelForm):
    """
    Form for adding/editing doctor profiles
    """
    class Meta:
        model = Doctor
        fields = [
            'doctor_id', 'full_name', 'specialization', 'gender',
            'phone_number', 'email', 'clinic_location', 'consultation_fee',
            'is_available', 'accepts_walkins', 'license_number',
            'years_of_experience', 'qualifications', 'bio'
        ]
        widgets = {
            'doctor_id': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., General Practice, Cardiology'
            }),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'clinic_location': forms.TextInput(attrs={'class': 'form-control'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'accepts_walkins': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'qualifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
        }


class DoctorScheduleForm(forms.ModelForm):
    """
    Form for managing doctor schedules
    """
    class Meta:
        model = DoctorSchedule
        fields = ['doctor', 'day_of_week', 'start_time', 'end_time', 
                 'slot_duration', 'is_active']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'day_of_week': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'slot_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 15,
                'step': 15
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
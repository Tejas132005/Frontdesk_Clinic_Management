from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Staff, Doctor


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']
        read_only_fields = ['id']


class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Staff
        fields = ['id', 'user', 'role', 'department', 'phone_number', 'is_active']
        read_only_fields = ['id']


class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'user', 'specialization', 'license_number', 'phone_number', 'is_active']
        read_only_fields = ['id']

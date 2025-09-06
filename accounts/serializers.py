from rest_framework import serializers
from accounts.models import *
from registration.models import Profile, Registration ,Payment
from django.utils import timezone




# auth_app/serializers.py
from rest_framework import serializers

class SendOtpSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=15)

class VerifyOtpSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone_number", "is_phone_verified"] 
        
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ["user", "created_at", "updated_at"]

class RegistrationSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = Registration
        fields = "__all__"

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"


class RegistrationStatusSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    profile_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Registration
        fields = [
            'id', 
            'status', 
            'submitted_at', 
            'user_phone', 
            'user_name',
            'profile_data'
        ]
    
    def get_profile_data(self, obj):
        if obj.profile:
            # Return essential profile data (adjust fields as needed)
            return {
                'full_name': getattr(obj.profile, 'full_name', ''),
                'email': getattr(obj.profile, 'email', ''),
                'address': getattr(obj.profile, 'address', ''),
                # Add other profile fields you need
            }
        return None 
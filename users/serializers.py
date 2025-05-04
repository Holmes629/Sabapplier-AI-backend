from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import user, Token

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = user
        fields = ['id', 'fullname', 'email', 'dateofbirth', 'password', 'phone_number', 'passport_size_photo_file_url', 'aadhaar_card_file_url', 'aadhaar_card_text', 'pan_card_file_url', 'pan_card_text', 'signature_file_url', '_10th_certificate_file_url', '_10th_certificate_text', '_12th_certificate_file_url', '_12th_certificate_text', 'graduation_certificate_file_url', 'graduation_certificate_text', 'address', 'city', 'state', 'country', 'pincode']

class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ["token", "created_at", "expires_at", "user_id", "is_used"]
        
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    # password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = user
        fields = ('fullname', 'email', 'password')

    # def validate(self, attrs):
    #     if attrs['password'] != attrs['password2']:
    #         raise serializers.ValidationError({"password": "Password fields didn't match."})
    #     return attrs

    def create(self, validated_data):
        validated_data.pop('password')
        if User.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError({'email': 'This email is already registered...'})
        user = User.objects.create_user(**validated_data)
        return user 
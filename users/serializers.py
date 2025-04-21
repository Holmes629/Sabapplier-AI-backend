from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import user, Token

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = user
        fields = ['id', 'username', 'email', 'password', 'phone_number', 'profile_photo', 'aadhaar_card', 'pan_card', 'address', 'city', 'state', 'country', 'pincode']

class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ["token", "created_at", "expires_at", "user_id", "is_used"]
        
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    # password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = user
        fields = ('username', 'email', 'password')

    # def validate(self, attrs):
    #     if attrs['password'] != attrs['password2']:
    #         raise serializers.ValidationError({"password": "Password fields didn't match."})
    #     return attrs

    def create(self, validated_data):
        validated_data.pop('password')
        if User.objects.filter(username=validated_data['username']).exists():
            raise serializers.ValidationError({'username': 'This username is already taken.'})
        user = User.objects.create_user(**validated_data)
        return user 
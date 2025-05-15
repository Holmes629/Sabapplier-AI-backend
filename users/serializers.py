from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import user, Token

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = user
        fields = ['fullname', 'email', 'dateofbirth', 'password', 'phone_number', 'passport_size_photo_file_url', 'aadhaar_card_file_url', 'aadhaar_card_text', 'pan_card_file_url', 'pan_card_text', 'signature_file_url', '_10th_certificate_file_url', '_10th_certificate_text', '_12th_certificate_file_url', '_12th_certificate_text', 'graduation_certificate_file_url', 'graduation_certificate_text', 'address', 'city', 'state', 'country', 'pincode']
        extra_kwargs = {
            'fullname': {'required': False, 'allow_null': True, 'allow_blank': True},
            'dateofbirth': {'required': False, 'allow_null': True},
            'phone_number': {'required': False, 'allow_null': True, 'allow_blank': True},
            'passport_size_photo_file_url': {'required': False, 'allow_null': True},
            'aadhaar_card_file_url': {'required': False, 'allow_null': True},
            'aadhaar_card_text': {'required': False, 'allow_null': True, 'allow_blank': True},
            'pan_card_file_url': {'required': False, 'allow_null': True},
            'pan_card_text': {'required': False, 'allow_null': True, 'allow_blank': True},
            'signature_file_url': {'required': False, 'allow_null': True},
            '_10th_certificate_file_url': {'required': False, 'allow_null': True},
            '_10th_certificate_text': {'required': False, 'allow_null': True, 'allow_blank': True},
            '_12th_certificate_file_url': {'required': False, 'allow_null': True},
            '_12th_certificate_text': {'required': False, 'allow_null': True, 'allow_blank': True},
            'graduation_certificate_file_url': {'required': False, 'allow_null': True},
            'graduation_certificate_text': {'required': False, 'allow_null': True, 'allow_blank': True},
            'address': {'required': False, 'allow_null': True, 'allow_blank': True},
            'city': {'required': False, 'allow_null': True, 'allow_blank': True},
            'state': {'required': False, 'allow_null': True, 'allow_blank': True},
            'country': {'required': False, 'allow_null': True, 'allow_blank': True},
            'pincode': {'required': False, 'allow_null': True},
            'password': {'write_only': True, 'required': True},
            'email': {'required': True},
        }

    def update(self, instance, validated_data):
        # Only update fields present in validated_data
        print(validated_data)
        for attr, value in validated_data.items():
            if attr == 'password':
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance

class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ["token", "created_at", "expires_at", "user_id", "is_used"]
        
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    email = serializers.EmailField(required=True)

    class Meta:
        model = user
        fields = ('email', 'password')

    def create(self, validated_data):
        if 'fullname' not in validated_data or validated_data.get('fullname') == 'undefined':
             validated_data['fullname'] = ""
        if user.objects.filter(email=validated_data['email']).exists():
             raise serializers.ValidationError({'email': 'This email is already registered...'})
        return user.objects.create(**validated_data) 
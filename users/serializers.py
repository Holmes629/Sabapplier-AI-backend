from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import user, Token

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = user
        fields = ['email', 'password', 'fullName', 'fathersName', 'mothersName', 'gender', 'dateofbirth', 'category', 'disability', 'nationality', 'domicileState', 'maritalStatus', 'religion', 'permanentAddress', 'correspondenceAddress', 'phone_number', 'alt_phone_number', 'google_profile_picture', 'document_urls', 'document_texts']
        # extra_kwargs = {
        #     'fullName': {'required': False, 'allow_null': True, 'allow_blank': True},
        #     'dateofbirth': {'required': False, 'allow_null': True},
        #     'phone_number': {'required': False, 'allow_null': True, 'allow_blank': True},
        #     'document_urls': {'required': False, 'allow_null': True},
        #     'document_texts': {'required': False, 'allow_null': True},
        #     'address': {'required': False, 'allow_null': True, 'allow_blank': True},
        #     'city': {'required': False, 'allow_null': True, 'allow_blank': True},
        #     'state': {'required': False, 'allow_null': True, 'allow_blank': True},
        #     'country': {'required': False, 'allow_null': True, 'allow_blank': True},
        #     'pincode': {'required': False, 'allow_null': True},
        #     'password': {'write_only': True, 'required': True},
        #     'email': {'required': True},
        # }

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
        if 'fullName' not in validated_data or validated_data.get('fullName') == 'undefined':
             validated_data['fullName'] = ""
        if user.objects.filter(email=validated_data['email']).exists():
             raise serializers.ValidationError({'email': 'This email is already registered...'})
        return user.objects.create(**validated_data) 
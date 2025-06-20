from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import user, Token

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    # Add individual document URL fields that map to the document_urls JSONField
    passport_size_photo_file_url = serializers.SerializerMethodField()
    aadhaar_card_file_url = serializers.SerializerMethodField()
    pan_card_file_url = serializers.SerializerMethodField()
    signature_file_url = serializers.SerializerMethodField()
    _10th_certificate_file_url = serializers.SerializerMethodField()
    _12th_certificate_file_url = serializers.SerializerMethodField()
    graduation_certificate_file_url = serializers.SerializerMethodField()
    left_thumb_file_url = serializers.SerializerMethodField()
    caste_certificate_file_url = serializers.SerializerMethodField()
    pwd_certificate_file_url = serializers.SerializerMethodField()
    domicile_certificate_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = user
        fields = ['email', 'password', 'fullName', 'fathersName', 'mothersName', 'gender', 'dateofbirth', 'category', 'disability', 'nationality', 'domicileState', 'maritalStatus', 'religion', 'permanentAddress', 'correspondenceAddress', 'phone_number', 'alt_phone_number', 'google_profile_picture', 'document_urls', 'document_texts',
                 'passport_size_photo_file_url', 'aadhaar_card_file_url', 'pan_card_file_url', 'signature_file_url', '_10th_certificate_file_url', '_12th_certificate_file_url', 'graduation_certificate_file_url', 'left_thumb_file_url', 'caste_certificate_file_url', 'pwd_certificate_file_url', 'domicile_certificate_file_url']

    def get_passport_size_photo_file_url(self, obj):
        return obj.document_urls.get('passport_size_photo_file_url') if obj.document_urls else None
    
    def get_aadhaar_card_file_url(self, obj):
        return obj.document_urls.get('aadhaar_card_file_url') if obj.document_urls else None
    
    def get_pan_card_file_url(self, obj):
        return obj.document_urls.get('pan_card_file_url') if obj.document_urls else None
    
    def get_signature_file_url(self, obj):
        return obj.document_urls.get('signature_file_url') if obj.document_urls else None
    
    def get__10th_certificate_file_url(self, obj):
        return obj.document_urls.get('_10th_certificate_file_url') if obj.document_urls else None
    
    def get__12th_certificate_file_url(self, obj):
        return obj.document_urls.get('_12th_certificate_file_url') if obj.document_urls else None
    
    def get_graduation_certificate_file_url(self, obj):
        return obj.document_urls.get('graduation_certificate_file_url') if obj.document_urls else None
    
    def get_left_thumb_file_url(self, obj):
        return obj.document_urls.get('left_thumb_file_url') if obj.document_urls else None
    
    def get_caste_certificate_file_url(self, obj):
        return obj.document_urls.get('caste_certificate_file_url') if obj.document_urls else None
    
    def get_pwd_certificate_file_url(self, obj):
        return obj.document_urls.get('pwd_certificate_file_url') if obj.document_urls else None
    
    def get_domicile_certificate_file_url(self, obj):
        return obj.document_urls.get('domicile_certificate_file_url') if obj.document_urls else None
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
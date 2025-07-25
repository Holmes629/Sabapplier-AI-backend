from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import user, Token, DataShare, ShareNotification
import uuid

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    # Add individual document fields for frontend compatibility
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
    
    # Expose all document_urls as a dictionary
    all_documents = serializers.SerializerMethodField()

    effective_successful_referrals = serializers.SerializerMethodField()

    class Meta:
        model = user
        fields = [
            'email', 'password', 'first_name', 'middle_name', 'last_name', 'fullName', 'fathersName', 'mothersName', 
            'gender', 'dateofbirth', 'category', 'disability', 'nationality', 
            'domicileState', 'district', 'mandal', 'pincode', 'maritalStatus', 'religion', 'permanentAddress', 
            'correspondenceAddress', 'phone_number', 'alt_phone_number',
            'google_profile_picture', 'document_urls', 'document_texts',
            'extra_details',
            # New autofill fields
            'hasChangedName', 'changedNameDetail', 'motherTongue',
            # Referral system fields
            'referral_code', 'referred_by', 'successful_referrals',
            # Individual document fields for frontend
            'passport_size_photo_file_url', 'aadhaar_card_file_url', 'pan_card_file_url',
            'signature_file_url', '_10th_certificate_file_url', '_12th_certificate_file_url',
            'graduation_certificate_file_url', 'left_thumb_file_url', 'caste_certificate_file_url',
            'pwd_certificate_file_url', 'domicile_certificate_file_url',
            # New: all documents
            'all_documents',
            # New: custom doc category mapping
            'custom_doc_categories',
            'highest_education',
            # New field for feature gating
            'effective_successful_referrals',
            # Website access fields
            'has_website_access',
        ]

    def _get_document_url(self, obj, field_name):
        """Helper method to get document URL, checking both new and legacy formats"""
        if not obj.document_urls:
            return None
        
        # First try the new format (direct field name)
        url = obj.document_urls.get(field_name)
        if url:
            return url
        
        # Then try the legacy format (email_prefix_field_name)
        email_prefix = obj.email.split('@')[0] if obj.email else ''
        legacy_key = f"{email_prefix}_{field_name}"
        return obj.document_urls.get(legacy_key)

    def get_passport_size_photo_file_url(self, obj):
        return self._get_document_url(obj, 'passport_size_photo_file_url')
    
    def get_aadhaar_card_file_url(self, obj):
        return self._get_document_url(obj, 'aadhaar_card_file_url')
    
    def get_pan_card_file_url(self, obj):
        return self._get_document_url(obj, 'pan_card_file_url')
    
    def get_signature_file_url(self, obj):
        return self._get_document_url(obj, 'signature_file_url')
    
    def get__10th_certificate_file_url(self, obj):
        return self._get_document_url(obj, '_10th_certificate_file_url')
    
    def get__12th_certificate_file_url(self, obj):
        return self._get_document_url(obj, '_12th_certificate_file_url')
    
    def get_graduation_certificate_file_url(self, obj):
        return self._get_document_url(obj, 'graduation_certificate_file_url')
    
    def get_left_thumb_file_url(self, obj):
        return self._get_document_url(obj, 'left_thumb_file_url')
    
    def get_caste_certificate_file_url(self, obj):
        return self._get_document_url(obj, 'caste_certificate_file_url')
    
    def get_pwd_certificate_file_url(self, obj):
        return self._get_document_url(obj, 'pwd_certificate_file_url')
    
    def get_domicile_certificate_file_url(self, obj):
        return self._get_document_url(obj, 'domicile_certificate_file_url')

    def get_all_documents(self, obj):
        print("DEBUG: document_urls =", obj.document_urls)
        docs = {}
        email_prefix = obj.email.split('@')[0] if obj.email else ''
        for k, v in (obj.document_urls or {}).items():
            print("DEBUG: key =", k, "value =", v)
            if k.startswith(email_prefix + '_'):
                norm_key = k[len(email_prefix) + 1:]
            else:
                norm_key = k
            docs[norm_key] = v
        print("DEBUG: all_documents to return =", docs)
        return docs
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
        # Optionally, update fullName for backward compatibility
        if (
            validated_data.get('first_name') or validated_data.get('last_name')
        ):
            instance.fullName = f"{validated_data.get('first_name', '')} {validated_data.get('middle_name', '')} {validated_data.get('last_name', '')}".strip()
        instance.save()
        return instance

    def get_effective_successful_referrals(self, obj):
        if getattr(obj, 'force_advanced_locked', False):
            return 0
        total_users = user.objects.count()
        if total_users < 100:
            return 2
        return obj.successful_referrals or 0

class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ["token", "created_at", "expires_at", "user_id", "is_used"]
        
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    email = serializers.EmailField(required=True)
    referred_by = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = user
        fields = ('email', 'password', 'referred_by', 'highest_education')

    def create(self, validated_data):
        if 'fullName' not in validated_data or validated_data.get('fullName') == 'undefined':
             validated_data['fullName'] = ""
        # Optionally, set fullName from first/middle/last name
        if (
            validated_data.get('first_name') or validated_data.get('last_name')
        ):
            validated_data['fullName'] = f"{validated_data.get('first_name', '')} {validated_data.get('middle_name', '')} {validated_data.get('last_name', '')}".strip()
        if user.objects.filter(email=validated_data['email']).exists():
             raise serializers.ValidationError({'email': 'This email is already registered...'})
        # Generate unique referral code
        referral_code = str(uuid.uuid4())[:8]
        validated_data['referral_code'] = referral_code
        referred_by = validated_data.pop('referred_by', None)
        if referred_by:
            validated_data['referred_by'] = referred_by
        new_user = user.objects.create(**validated_data)
        # If referred_by is valid, increment inviter's successful_referrals
        if referred_by:
            inviter = user.objects.filter(referral_code=referred_by).first()
            if inviter:
                inviter.successful_referrals += 1
                inviter.save()
        return new_user

class DataShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataShare
        fields = ['id', 'sender_email', 'receiver_email', 'status', 'is_active', 
                 'shared_at', 'responded_at', 'stopped_at', 'shared_data']
        read_only_fields = ['id', 'shared_at', 'responded_at', 'stopped_at', 'shared_data']

class ShareNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShareNotification
        fields = ['id', 'data_share', 'recipient_email', 'notification_type', 
                 'message', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']
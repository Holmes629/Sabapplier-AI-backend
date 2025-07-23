from django.db import models
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string

def generate_unique_referral_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not user.objects.filter(referral_code=code).exists():
            return code


class Token(models.Model):
    id = models.AutoField(primary_key=True)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    user_id = models.IntegerField()
    is_used = models.BooleanField(default=False)
    
class DataShare(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('stopped', 'Stopped'),
    ]
    
    sender_email = models.EmailField()  # User who shares their data
    receiver_email = models.EmailField()  # Friend who receives the data
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True)  # Sender can control this
    shared_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    stopped_at = models.DateTimeField(null=True, blank=True)
    
    # Store shared data at the time of sharing (snapshot)
    shared_data = models.JSONField(default=dict, blank=True)  # Complete user data snapshot
    selected_documents = models.JSONField(default=list, blank=True)  # List of document types user selected to share
    

    
    class Meta:
        unique_together = ('sender_email', 'receiver_email')  # Prevent duplicate shares
    
    def __str__(self):
        return f"{self.sender_email} -> {self.receiver_email} ({self.status})"
    
    def save_shared_data(self, user_instance, sharing_type="documents_only"):
        """Save a snapshot of user's data for sharing, based on sharing_type."""
        selected_document_urls = {}
        selected_document_texts = {}
        if self.selected_documents and len(self.selected_documents) > 0 and user_instance.document_urls:
            for doc_type in self.selected_documents:
                if doc_type in user_instance.document_urls and user_instance.document_urls[doc_type]:
                    selected_document_urls[doc_type] = user_instance.document_urls[doc_type]
                if user_instance.document_texts and doc_type in user_instance.document_texts:
                    selected_document_texts[doc_type] = user_instance.document_texts[doc_type]
        sharing_metadata = {
            'sharing_type': sharing_type,
            'selected_documents': self.selected_documents,
            'total_selected_documents': len(self.selected_documents) if self.selected_documents else 0,
            'total_available_documents': len([k for k, v in (user_instance.document_urls or {}).items() if v]),
            'shared_documents_count': len(selected_document_urls),
            'includes_documents': len(selected_document_urls) > 0,
        }
        if sharing_type == "documents_only":
            self.shared_data = {
                'documents': {
                    'document_urls': selected_document_urls,
                    'document_texts': selected_document_texts,
                },
                'sharing_metadata': sharing_metadata,
                'timestamp': self.shared_at.isoformat() if self.shared_at else None,
            }
        else:
            self.shared_data = {
                'personal_info': {
                    'fullName': user_instance.fullName,
                    'fathersName': user_instance.fathersName,
                    'mothersName': user_instance.mothersName,
                    'gender': user_instance.gender,
                    'dateofbirth': user_instance.dateofbirth.isoformat() if user_instance.dateofbirth else None,
                    'category': user_instance.category,
                    'disability': user_instance.disability,
                    'nationality': user_instance.nationality,
                    'domicileState': user_instance.domicileState,
                    'district': user_instance.district,
                    'mandal': user_instance.mandal,
                    'pincode': user_instance.pincode,
                    'maritalStatus': user_instance.maritalStatus,
                    'religion': user_instance.religion,
                    'phone_number': user_instance.phone_number,
                    'alt_phone_number': user_instance.alt_phone_number,
                },
                'addresses': {
                    'permanentAddress': user_instance.permanentAddress,
                    'correspondenceAddress': user_instance.correspondenceAddress,
                },
                'documents': {
                    'document_urls': selected_document_urls,
                    'document_texts': selected_document_texts,
                },
                'profile': {
                    'google_profile_picture': user_instance.google_profile_picture,
                },
                'sharing_metadata': sharing_metadata,
                'timestamp': self.shared_at.isoformat() if self.shared_at else None,
            }
        self.save()

class ShareNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('share_request', 'Share Request'),
        ('share_accepted', 'Share Accepted'),
        ('share_declined', 'Share Declined'),
        ('share_stopped', 'Share Stopped'),
    ]
    
    data_share = models.ForeignKey(DataShare, on_delete=models.CASCADE, related_name='notifications')
    recipient_email = models.EmailField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.notification_type} for {self.recipient_email}"

def passport_size_photo_upload_path(instance, filename):
    ext = filename.split('.')[-1] # Get the file extension
    filename = f"{instance.email.split('@')[0]}_passport_size_photo.{ext}" 
    return os.path.join("passport_size_photos", filename)

def aadhaar_card_upload_path(instance, filename):
    ext = filename.split('.')[-1] # Get the file extension
    filename = f"{instance.email.split('@')[0]}_aadhaar_card.{ext}" 
    return os.path.join("aadhaar_cards", filename)

def pan_card_upload_path(instance, filename):
    ext = filename.split('.')[-1] # Get the file extension
    filename = f"{instance.email.split('@')[0]}_pan_card.{ext}" 
    return os.path.join("pan_cards", filename)

def signature_upload_path(instance, filename):
    ext = filename.split('.')[-1] # Get the file extension
    filename = f"{instance.email.split('@')[0]}_signature.{ext}" 
    return os.path.join("signatures", filename)

def _10th_certificate_upload_path(instance, filename):
    ext = filename.split('.')[-1] # Get the file extension
    filename = f"{instance.email.split('@')[0]}_10th_certificate.{ext}" 
    return os.path.join("_10th_certificates", filename)

def _12th_certificate_upload_path(instance, filename):
    ext = filename.split('.')[-1] # Get the file extension
    filename = f"{instance.email.split('@')[0]}_12th_certificate.{ext}" 
    return os.path.join("_12th_certificates", filename)

def graduation_certificate_upload_path(instance, filename):
    ext = filename.split('.')[-1] # Get the file extension
    filename = f"{instance.email.split('@')[0]}_graduation_certificate.{ext}" 
    return os.path.join("graduation_certificate", filename)
   
class user(models.Model):     
    Gender_Choices = [
        ('Select', 'Select'),
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    Category_Choices = [
        ('Select', 'Select'),
        ('GEN', 'GEN'),
        ('OBC', 'OBC'),
        ('SC', 'SC'),
        ('ST', 'ST'),
        ('EWS', 'EWS'),
    ]
    MaritalStatus_Choices = [
        ('Select', 'Select'),
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed'),
        ('Others', 'Others'),
    ]
    Education_Choices = [
        ('', 'Select'),
        ('Matriculation (10th)', 'Matriculation (10th)'),
        ('Higher Secondary (10+2)', 'Higher Secondary (10+2)'),
        ('Diploma', 'Diploma'),
        ('Graduation', 'Graduation'),
        ('Post Graduation', 'Post Graduation'),
        ('Ph.D', 'Ph.D'),
    ]
    # Required fields (no null/blank):
    email = models.EmailField(unique=True, null=True, blank=True)
    force_advanced_locked = models.BooleanField(default=False, help_text="Force advanced features to be locked for this user")
    has_website_access = models.BooleanField(default=False, help_text="Enable access to the main application")
    password = models.CharField(max_length=255, null=True, blank=True)
    fullName = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    dateofbirth = models.DateField(null=True, blank=True)
    correspondenceAddress = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    # All other fields optional:
    fathersName = models.CharField(max_length=255, null=True, blank=True)
    mothersName = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender_Choices, default='Select', null=True, blank=True)
    hasChangedName = models.CharField(max_length=5, choices=[('Yes', 'Yes'), ('No', 'No')], null=True, blank=True)
    changedNameDetail = models.CharField(max_length=255, null=True, blank=True)
    motherTongue = models.CharField(max_length=255, null=True, blank=True)
    referral_code = models.CharField(max_length=32, unique=True, null=True, blank=True)
    referred_by = models.CharField(max_length=32, null=True, blank=True)
    successful_referrals = models.IntegerField(default=0, null=True, blank=True)
    category = models.CharField(max_length=10, choices=Category_Choices, default='Select', null=True, blank=True)
    disability = models.BooleanField(default=False, null=True, blank=True)
    nationality = models.CharField(max_length=255, null=True, blank=True)
    domicileState = models.CharField(max_length=255, null=True, blank=True)
    district = models.CharField(max_length=255, null=True, blank=True)
    mandal = models.CharField(max_length=255, null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)
    maritalStatus = models.CharField(max_length=255, choices=MaritalStatus_Choices, default='Select', null=True, blank=True)
    religion = models.CharField(max_length=255, null=True, blank=True)
    permanentAddress = models.TextField(null=True, blank=True)
    alt_phone_number = models.CharField(max_length=20, null=True, blank=True)
    google_profile_picture = models.URLField(null=True, blank=True)
    document_urls = models.JSONField(default=dict, null=True, blank=True)
    document_texts = models.JSONField(default=dict, null=True, blank=True)
    extra_details = models.JSONField(default=list, null=True, blank=True)
    custom_doc_categories = models.JSONField(default=dict, null=True, blank=True)
    highest_education = models.CharField(max_length=32, choices=Education_Choices, null=True, blank=True)

    def __str__(self):
        return self.email


class ContactUsRequest(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} <{self.email}>: {self.subject} ({self.created_at})"

class AccessController(models.Model):
    email = models.ForeignKey('user', on_delete=models.CASCADE, related_name='access_controllers', null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    force_advanced_locked = models.BooleanField(default=False)
    has_website_access = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=32, null=True, blank=True)
    referred_by = models.CharField(max_length=32, null=True, blank=True)
    successful_referrals = models.IntegerField(default=0, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AccessController for {self.email}" 

    def save(self, *args, **kwargs):
        # Sync to related user if email is set
        if self.email:
            user_changed = False
            if not self.referral_code:
                self.referral_code = generate_unique_referral_code()
            if self.email.force_advanced_locked != self.force_advanced_locked:
                self.email.force_advanced_locked = self.force_advanced_locked
                user_changed = True
            if self.email.has_website_access != self.has_website_access:
                self.email.has_website_access = self.has_website_access
                user_changed = True
            if self.email.referral_code != self.referral_code:
                self.email.referral_code = self.referral_code
                user_changed = True
            if self.email.referred_by != self.referred_by:
                self.email.referred_by = self.referred_by
                user_changed = True
            if self.email.successful_referrals != self.successful_referrals:
                self.email.successful_referrals = self.successful_referrals
                user_changed = True
            if user_changed:
                self.email.save()
        super().save(*args, **kwargs)

@receiver(post_save, sender=user)
def sync_user_to_accesscontroller(sender, instance, **kwargs):
    # Update all related AccessController objects to match the user fields
    for ac in instance.access_controllers.all():
        changed = False
        if ac.force_advanced_locked != instance.force_advanced_locked:
            ac.force_advanced_locked = instance.force_advanced_locked
            changed = True
        if ac.has_website_access != instance.has_website_access:
            ac.has_website_access = instance.has_website_access
            changed = True
        if ac.referral_code != instance.referral_code:
            ac.referral_code = instance.referral_code
            changed = True
        if ac.referred_by != instance.referred_by:
            ac.referred_by = instance.referred_by
            changed = True
        if ac.successful_referrals != instance.successful_referrals:
            ac.successful_referrals = instance.successful_referrals
            changed = True
        if changed:
            ac.save()

@receiver(post_save, sender=user)
def create_accesscontroller_for_user(sender, instance, created, **kwargs):
    if created:
        # Only create if not already present
        if not hasattr(instance, 'access_controllers') or instance.access_controllers.count() == 0:
            AccessController.objects.create(
                email=instance,
                force_advanced_locked=instance.force_advanced_locked,
                has_website_access=instance.has_website_access,
                referral_code=instance.referral_code,
                referred_by=instance.referred_by,
                successful_referrals=instance.successful_referrals,
            )

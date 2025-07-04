from django.db import models
import os

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
    
    def save_shared_data(self, user_instance):
        """Save a snapshot of user's autofill and OCR data"""
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
                'document_urls': user_instance.document_urls,
                'document_texts': user_instance.document_texts,  # OCR extracted data
            },
            'profile': {
                'google_profile_picture': user_instance.google_profile_picture,
            },
            'sharing_metadata': {
                'selected_documents': self.selected_documents,  # Which documents user chose to share
                'total_available_documents': len([k for k, v in (user_instance.document_urls or {}).items() if v]),
            },
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
    
      # id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    fullName = models.CharField(max_length=255, null=True)
    fathersName = models.CharField(max_length=255, null=True)
    mothersName = models.CharField(max_length=255, null=True)
    gender = models.CharField(max_length=10, choices=Gender_Choices, default='Select')
    dateofbirth = models.DateField(null=True)
    category = models.CharField(max_length=10, choices=Category_Choices, default='Select')
    disability = models.BooleanField(default=False)
    nationality = models.CharField(max_length=255, null=True)
    domicileState = models.CharField(max_length=255, null=True)
    district = models.CharField(max_length=255, null=True)
    mandal = models.CharField(max_length=255, null=True)
    pincode = models.CharField(max_length=6, null=True)
    maritalStatus = models.CharField(max_length=255, choices=MaritalStatus_Choices, default='Select')
    religion = models.CharField(max_length=255, null=True)
    permanentAddress = models.TextField(null=True)
    correspondenceAddress = models.TextField(null=True)
    phone_number = models.CharField(max_length=10, null=True)
    alt_phone_number = models.CharField(max_length=10, null=True)
    google_profile_picture = models.URLField(null=True, blank=True)  # Store Google profile picture URL
    document_urls = models.JSONField(default=dict, null=True)
    document_texts = models.JSONField(default=dict, null=True)

    def __str__(self):
        return self.email

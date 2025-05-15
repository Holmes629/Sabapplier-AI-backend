from django.db import models
from .dropbox_storage import DropboxStorage  # import your custom storage
import os

# Define drop box storage
dropbox_storage = DropboxStorage()

class Token(models.Model):
    id = models.AutoField(primary_key=True)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    user_id = models.IntegerField()
    is_used = models.BooleanField(default=False)
    
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
    # id = models.AutoField(primary_key=True)
    fullname = models.CharField(max_length=255, null=True)
    email = models.EmailField(unique=True)
    dateofbirth = models.DateField(null=True)
    password = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=10, null=True)
    passport_size_photo_file_url =models.FileField(upload_to=passport_size_photo_upload_path, storage=dropbox_storage, null=True)
    aadhaar_card_file_url = models.FileField(upload_to=aadhaar_card_upload_path, storage=dropbox_storage, null=True)
    aadhaar_card_text = models.TextField(null=True)
    pan_card_file_url = models.FileField(upload_to=pan_card_upload_path, storage=dropbox_storage, null=True)
    pan_card_text = models.TextField(null=True)
    signature_file_url =  models.FileField(upload_to=signature_upload_path, storage=dropbox_storage, null=True)
    _10th_certificate_file_url = models.FileField(upload_to=_10th_certificate_upload_path, storage=dropbox_storage, null=True)
    _10th_certificate_text = models.TextField(null=True)
    _12th_certificate_file_url = models.FileField(upload_to=_12th_certificate_upload_path, storage=dropbox_storage, null=True)
    _12th_certificate_text = models.TextField(null=True)
    graduation_certificate_file_url = models.FileField(upload_to=graduation_certificate_upload_path, storage=dropbox_storage, null=True)
    graduation_certificate_text = models.TextField(null=True)
    address = models.TextField(null=True)
    city = models.CharField(max_length=150, null=True)
    state = models.CharField(max_length=150, null=True)
    country = models.CharField(max_length=63, null=True)
    pincode = models.IntegerField(null=True)

    def __str__(self):
        return self.email

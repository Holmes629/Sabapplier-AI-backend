from django.db import models
from gdstorage.storage import GoogleDriveStorage
import os

# Define Google Drive Storage
gd_storage = GoogleDriveStorage()


class Token(models.Model):
    id = models.AutoField(primary_key=True)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    user_id = models.IntegerField()
    is_used = models.BooleanField(default=False)
    
def profile_photo_upload_path(instance, filename):
    ext = filename.split('.')[-1] # Get the file extension
    filename = f"{instance.email.split('@')[0]}_profile_photo.{ext}" # Create new filename: <user_email>_aadhaar_card.<ext>
    return os.path.join("profile_photos", filename)

def aadhaar_card_upload_path(instance, filename):
    ext = filename.split('.')[-1] # Get the file extension
    filename = f"{instance.email.split('@')[0]}_aadhaar_card.{ext}" # Create new filename: <user_email>_aadhaar_card.<ext>
    return os.path.join("aadhaar_cards", filename)

def pan_card_upload_path(instance, filename):
    ext = filename.split('.')[-1] # Get the file extension
    filename = f"{instance.email.split('@')[0]}_pan_card.{ext}" # Create new filename: <user_email>_aadhaar_card.<ext>
    return os.path.join("pan_cards", filename)
   
class user(models.Model):     
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=10, null=True)
    profile_photo=models.FileField(upload_to=profile_photo_upload_path, storage=gd_storage, null=True)
    aadhaar_card=models.FileField(upload_to=aadhaar_card_upload_path, storage=gd_storage, null=True)
    pan_card=models.FileField(upload_to=pan_card_upload_path, storage=gd_storage, null=True)
    address=models.TextField(null=True)
    city=models.CharField(max_length=150, null=True)
    state=models.CharField(max_length=150, null=True)
    country=models.CharField(max_length=63, null=True)
    pincode=models.IntegerField(null=True)

    def __str__(self):
        return self.username

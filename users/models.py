from django.db import models


class Token(models.Model):
    id = models.AutoField(primary_key=True)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    user_id = models.IntegerField()
    is_used = models.BooleanField(default=False)
    
    
class user(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=10, null=True)
    profile_photo=models.FileField(upload_to='profile_photos/', null=True)
    aadhaar_card=models.FileField(upload_to='aadhaar_cards/', null=True)
    pan_card=models.FileField(upload_to='pan_cards/', null=True)
    address=models.TextField(null=True)
    city=models.CharField(max_length=150, null=True)
    state=models.CharField(max_length=150, null=True)
    country=models.CharField(max_length=63, null=True)
    pincode=models.IntegerField(null=True)

    def __str__(self):
        return self.username

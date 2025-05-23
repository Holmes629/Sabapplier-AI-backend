# Generated by Django 5.1.7 on 2025-03-26 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='users',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_name', models.CharField(max_length=150)),
                ('password', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=150)),
                ('phone_number', models.IntegerField()),
                ('profile_photo', models.ImageField(upload_to='profile_photos/')),
                ('aadhaar_card', models.ImageField(upload_to='aadhaar_cards/')),
                ('pan_card', models.ImageField(upload_to='pan_cards/')),
                ('address', models.TextField()),
                ('city', models.CharField(max_length=150)),
                ('state', models.CharField(max_length=150)),
                ('country', models.CharField(max_length=150)),
                ('pincode', models.IntegerField()),
            ],
        ),
    ]

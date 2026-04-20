from django.db import models
from django.contrib.auth.models import AbstractUser
from .constants import ROLE_CHOICES,GENDER
import random
from datetime import timedelta
from django.utils import timezone
import random

# Create your models here.


class User(AbstractUser):
    username = models.CharField(max_length=8, unique=True,blank=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50,choices=ROLE_CHOICES,default="user")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


    def generate_unique_username(self):
        while True:
            username = str(random.randint(10000000, 99999999))
            if not User.objects.filter(username=username).exists():
                return username

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.generate_unique_username()
        super().save(*args, **kwargs)




class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    full_name = models.CharField(max_length=200,blank=True,null=True)
    gender = models.CharField(max_length=50,choices=GENDER,blank=True,null=True)
    contact_number = models.CharField(max_length=20,null=True, blank=True)
    skin_type = models.CharField(max_length=50,null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='Media/Profile/',blank=True,null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




class PasswordReserOTP(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def save(self,*args, **kwargs):
        if not self.otp:
            self.otp = str(random.randint(1000,9999))
        super().save(*args, **kwargs)

    
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"{self.user.email} - {self.otp}"
    

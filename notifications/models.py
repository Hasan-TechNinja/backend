from django.db import models
from account.models import User


# Create your models here.

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    body = models.TextField()
    data = models.JSONField(blank=True, null=True)
    read = models.BooleanField(default=False)
    admin_notification = models.BooleanField(default=False,blank=True, null=True)
    user_notification = models.BooleanField(default=False,blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"

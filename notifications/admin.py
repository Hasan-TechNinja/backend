from django.contrib import admin
from .models import Notification

# Register your models here.

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'read',"admin_notification","user_notification", 'created_at', 'updated_at')
    list_filter = ('read', 'created_at')
    search_fields = ('user__username', 'title', 'body')
    ordering = ('-created_at',)
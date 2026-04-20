from django.contrib import admin
from .models import User,Profile,PasswordReserOTP
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.


#admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["id", "username", "email", "role", "is_staff", "is_active"]
    search_fields =["email", "username"]
    list_filter =["role", "is_staff", "is_active"]

    ordering = ["-id"]

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Permissions", {"fields": ("role", "is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Custom Fields", {"fields": ("role",)}),
    )




@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["id","user","full_name","gender","contact_number","skin_type","date_of_birth","created_at",]

    search_fields = ["full_name","contact_number","user__email","user__username",]

    list_filter = ["gender","skin_type","created_at",]

    ordering = ["-created_at"]

    readonly_fields = ["created_at", "updated_at"]



@admin.register(PasswordReserOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'created_at', 'is_verified')
    search_fields = ('user__email', 'otp')
    list_filter = ('is_verified',)
    ordering = ('created_at',)



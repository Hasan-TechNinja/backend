from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import User, Profile, PasswordResetOTP, RegisterOTP
from django.core.mail import EmailMultiAlternatives
from datetime import timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)



@shared_task
def send_otp_email(user_id, otp):
    logger.info(f"Preparing to send OTP email to user {user_id}. OTP: {otp}")
    try:
        user = User.objects.get(id=user_id)
        send_mail(
            subject="Your OTP Code",
            message=f"Hello {user.username}, your OTP is: {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            # fail_silently=False,
        )
        logger.info(f"OTP email sent successfully to {user.email}")
        return f"OTP sent to {user.email}"
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found for OTP email")
        return "User not found"
    except Exception as e:
        logger.error(f"Failed to send OTP email to user {user_id}: {str(e)}")
        return f"Error: {str(e)}"
    


@shared_task
def send_welcome_email(user_id, lean="EN"):
    try:
        from .email_templates import get_welcome_email_en, get_welcome_email_ar

        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)

        full_name = profile.full_name or user.username
        phone = profile.contact_number or ''
        membership_id = user.username
        # Generate Circle ID: GC-XXXX from last 4 digits of membership ID
        circle_id = f"GC-{membership_id}"
        year = user.date_joined.year

        if lean == "AR":
            subject = "مرحبًا بك في Glowmi Circle ✨"
            html_message = get_welcome_email_ar(
                full_name, user.email, phone, membership_id, circle_id, year
            )
        else:
            subject = "Welcome to Glowmi Circle ✨"
            html_message = get_welcome_email_en(
                full_name, user.email, phone, membership_id, circle_id, year
            )

        email = EmailMultiAlternatives(
            subject=subject,
            body="Welcome to Glowmi Circle",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )

        email.attach_alternative(html_message, "text/html")
        email.send()
        return f"Welcome email sent to {user.email}"

    except User.DoesNotExist:
        return "User not found"



@shared_task
def cleanup_expired_otps():
    expired = PasswordResetOTP.objects.filter(
        is_verified=False,
        created_at__lt=timezone.now() - timedelta(minutes=3)
    )
    count = expired.count()
    expired.delete()
    return f"{count} expired OTPs deleted"
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import PasswordReserOTP, User
from datetime import timedelta
from django.utils import timezone
from .models import User, Profile
from django.core.mail import EmailMultiAlternatives



@shared_task
def send_otp_email(user_id, otp):
    print("TASK STARTED")
    try:
        user = User.objects.get(id=user_id)
        send_mail(
            subject="Your OTP Code",
            message=f"Hello {user.username}, your OTP is: {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        print("EMAIL SENT")
        return f"OTP sent to {user.email}"
    except User.DoesNotExist:
        return "User not found"
    


@shared_task
def send_welcome_email(user_id, lean="EN"):
    try:
        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)

        if lean == "AR":
            subject = "مرحبًا بك في Glowmi ✨"

            html_message = f"""
            <html dir="rtl">
            <body style="font-family: Arial; line-height:1.6; text-align:right;">

                <h2>مرحبًا {profile.full_name or user.username} 👋</h2>

                <p>نحن سعداء بانضمامك إلى <b>Glowmi</b>. شكرًا لانضمامك إلى مجتمعنا.</p>

                <h3>📋 معلوماتك:</h3>

                <table style="border-collapse: collapse;">
                    <tr>
                        <td><b>رقم العضوية:</b></td>
                        <td style="padding-right:10px;">{user.username}</td>
                    </tr>
                    <tr>
                        <td><b>الاسم:</b></td>
                        <td style="padding-right:10px;">{profile.full_name or ''}</td>
                    </tr>
                    <tr>
                        <td><b>البريد الإلكتروني:</b></td>
                        <td style="padding-right:10px;">{user.email}</td>
                    </tr>
                    <tr>
                        <td><b>الهاتف:</b></td>
                        <td style="padding-right:10px;">{profile.contact_number or ''}</td>
                    </tr>
                </table>

                <p>سيستخدم فريقنا هذه المعلومات لتقديم تجربة عناية بالبشرة أفضل لك.</p>

                <p>مع أطيب التحيات،<br><b>فريق Glowmi ✨</b></p>

            </body>
            </html>
            """

        else:
            subject = "Welcome to Glowmi ✨"

            html_message = f"""
            <html>
            <body style="font-family: Arial; line-height:1.6;">

                <h2>Hello {profile.full_name or user.username} 👋</h2>

                <p>We are excited to welcome you to <b>Glowmi</b>. Thanks for joining us.</p>

                <h3>📋 Your Information:</h3>

                <table style="border-collapse: collapse;">
                    <tr>
                        <td><b>Membership ID:</b></td>
                        <td style="padding-left:10px;">{user.username}</td>
                    </tr>
                    <tr>
                        <td><b>Name:</b></td>
                        <td style="padding-left:10px;">{profile.full_name or ''}</td>
                    </tr>
                    <tr>
                        <td><b>Email:</b></td>
                        <td style="padding-left:10px;">{user.email}</td>
                    </tr>
                    <tr>
                        <td><b>Phone:</b></td>
                        <td style="padding-left:10px;">{profile.contact_number or ''}</td>
                    </tr>
                </table>

                <p>We will use this information to provide you with a better skincare experience.</p>

                <p>Best Regards,<br><b>Glowmi Team ✨</b></p>

            </body>
            </html>
            """

        email = EmailMultiAlternatives(
            subject=subject,
            body="Welcome to Glowmi",  # fallback text
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
    expired = PasswordReserOTP.objects.filter(
        is_verified=False,
        created_at__lt=timezone.now() - timedelta(minutes=5)
    )
    count = expired.count()
    expired.delete()
    return f"{count} expired OTPs deleted"
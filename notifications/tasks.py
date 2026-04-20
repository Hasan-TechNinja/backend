from celery import shared_task
from notifications.models import Notification
from account.models import User
from .utils import send_realtime_notification

@shared_task
def create_notification_task(user_id, title, body, data=None,broadcast_admin=False,broadcast_user=False,broadcast_all=False):
    print("============hello")
    try:
        user = User.objects.get(id=user_id)
        
        notification = Notification.objects.create(
            user=user,
            title=title,
            body=body,
            data=data or {},
            admin_notification=broadcast_admin,
            user_notification=broadcast_user
        )
        if broadcast_user:
            user_id = user_id
        else:
            user_id=None

        send_realtime_notification(user_id, title, body, data,event_type="notification",broadcast_admin=broadcast_admin,broadcast_all=broadcast_all)

        return f"Notification created and pushed for user {user_id}"

    except User.DoesNotExist:
        return "User not found"


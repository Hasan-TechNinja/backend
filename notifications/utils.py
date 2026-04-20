from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_realtime_notification(user_id, title, body, data=None,event_type="notification",broadcast_admin=False,broadcast_all=False):
    channel_layer = get_channel_layer()

    payload = {
            "type": "send_notification",
            "data": {
                "event_type": event_type,
                "title": title,
                "body": body,
                "data": data or {},
                "read": False,
            }
        }

    if broadcast_all:
        if broadcast_all:
            async_to_sync(channel_layer.group_send)(
                "all_users", payload
            )
    else:
        if user_id:
            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}", payload
            )

    if broadcast_admin:
        async_to_sync(channel_layer.group_send)(
            "admin_notifications", payload
        )
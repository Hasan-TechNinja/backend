from django.urls import re_path, path
from . import consumers as notifications_consumers
from shop import consumers as shop_consumers

websocket_urlpatterns = [
    re_path(r"ws/notifications/", notifications_consumers.NotificationConsumer.as_asgi()),
    path("ws/chat/", shop_consumers.AIChatConsumer.as_asgi())
]
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import asyncio
# from truck.models import Truck
# from booking.models import Booking


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close()
            return

        self.group_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        if getattr(user, "role", None) == "admin":
            await self.channel_layer.group_add("admin_notifications", self.channel_name)


        await self.channel_layer.group_add("all_users", self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        user = self.scope.get("user")
        if user and getattr(user, "role", None) == "admin":
            await self.channel_layer.group_discard("admin_notifications", self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["data"]))

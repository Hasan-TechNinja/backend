import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import ChatSession, ChatMessage, GeneratedRoutine
from .catalog import build_product_catalog, get_catalog_product
from account.models import Profile
from . import ai_engine
from PIL import Image
import io
import base64

User = get_user_model()

MAX_IMAGE_BYTES = 10 * 1024 * 1024


class AIChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope.get("user")

            if not self.user or getattr(self.user, 'is_anonymous', True):
                await self.close()
                return

            await self.accept()

            # Load or create chat session
            self.session_id = await self.get_or_create_session(self.user.id)
        except Exception:
            logging.exception("Chat connect failed")
            await self.close()

    async def disconnect(self, close_code):
        pass

    def _base_url(self):
        headers = dict(self.scope.get("headers") or [])
        host = headers.get(b"x-forwarded-host") or headers.get(b"host") or b""
        proto = headers.get(b"x-forwarded-proto")
        if proto:
            scheme = proto.decode().split(",")[0].strip()
        else:
            scheme = "https" if self.scope.get("scheme") in ("wss", "https") else "http"
        return f"{scheme}://{host.decode()}" if host else ""

    @staticmethod
    def _decode_image(image_b64):
        if not image_b64:
            return None
        try:
            if "," in image_b64:
                image_b64 = image_b64.split(",", 1)[1]
            img_data = base64.b64decode(image_b64)
            if len(img_data) > MAX_IMAGE_BYTES:
                return None
            return Image.open(io.BytesIO(img_data))
        except Exception as e:
            logging.error(f"Image decode error: {e}")
            return None

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload, ensure_ascii=False))

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
            message = (data.get('message') or data.get('content') or data.get('text') or '').strip()
            image_b64 = data.get('photo') or data.get('image_b64')
            language = 'ar' if str(data.get('language', '')).lower().startswith('ar') else 'en'

            if not message and not image_b64:
                return

            pil_image = self._decode_image(image_b64)

            user_profile = await self.build_user_profile(self.user.id)
            product_catalog = await self.build_product_catalog()
            chat_history = await self.get_chat_history(self.session_id)
            summary_anchor = await self.get_summary_anchor(self.session_id)

            metadata = None
            async for chunk in ai_engine.stream_chat_assistant(
                user_profile=user_profile,
                chat_history=chat_history,
                current_prompt=message,
                product_catalog=product_catalog,
                summary_anchor=summary_anchor,
                image=pil_image,
                language=language,
            ):
                if isinstance(chunk, str):
                    await self.send_json({'type': 'chunk', 'role': 'assistant', 'content': chunk})
                else:
                    metadata = chunk

            if not metadata:
                return

            reply = metadata.full_response
            is_for_friend = metadata.is_for_friend
            stored_user_message = message or ("(شاركت صورة)" if language == 'ar' else "(Shared a photo)")

            # Refresh long-term memory every 10 messages to save quota
            if not is_for_friend and len(chat_history) >= 10 and len(chat_history) % 10 == 0:
                updated_anchor = await ai_engine.update_summary_anchor(
                    user_profile=user_profile,
                    chat_history=chat_history + [
                        {"role": "user", "content": stored_user_message},
                        {"role": "assistant", "content": reply},
                    ],
                    current_anchor=summary_anchor
                )
            else:
                updated_anchor = summary_anchor

            await self.save_exchange(self.session_id, stored_user_message, reply, is_for_friend, updated_anchor)

            products = []
            for ref in metadata.product_references:
                product = get_catalog_product(product_catalog, ref.product_id)
                if product:
                    products.append({
                        "id": product["id"],
                        "name": product["name"],
                        "category": product["category"],
                        "price": product["price"],
                        "image_url": product["image_url"],
                        "product_url": product["product_url"],
                    })

            await self.send_json({
                'type': 'final',
                'role': 'assistant',
                'response': reply,
                'is_for_friend': is_for_friend,
                'products': products,
                'triggers_routine': metadata.triggers_routine,
            })

        except json.JSONDecodeError:
            await self.send_json({"type": "error", "error": "Invalid JSON format."})
        except Exception:
            logging.exception("Chat receive failed")
            await self.send_json({"type": "error", "error": "Something went wrong. Please try again."})

    @database_sync_to_async
    def get_or_create_session(self, user_id):
        session, _ = ChatSession.objects.get_or_create(user_id=user_id)
        return session.id

    @database_sync_to_async
    def get_summary_anchor(self, session_id):
        session = ChatSession.objects.get(id=session_id)
        return session.summary_anchor

    @database_sync_to_async
    def get_chat_history(self, session_id):
        messages = list(ChatMessage.objects.filter(session_id=session_id).order_by('-created_at')[:30])
        messages.reverse()
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    @database_sync_to_async
    def save_exchange(self, session_id, user_msg, assistant_msg, is_for_friend, updated_anchor):
        if user_msg:
            ChatMessage.objects.create(session_id=session_id, role='user', content=user_msg, is_for_friend=is_for_friend)
        if assistant_msg:
            ChatMessage.objects.create(session_id=session_id, role='assistant', content=assistant_msg, is_for_friend=is_for_friend)

        if not is_for_friend:
            ChatSession.objects.filter(id=session_id).update(summary_anchor=updated_anchor)

    @database_sync_to_async
    def build_user_profile(self, user_id):
        """Only facts the user has actually given us (profile + latest skin analysis)."""
        user = User.objects.get(id=user_id)
        profile = Profile.objects.filter(user_id=user_id).first()
        latest = GeneratedRoutine.objects.filter(user_id=user_id).order_by('-created_at').first()
        intake = (latest.skin_profile or {}) if latest else {}

        age = intake.get("age")
        if profile and profile.date_of_birth:
            today = timezone.now().date()
            dob = profile.date_of_birth
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        return {
            "full_name": (profile.full_name if profile and profile.full_name else user.get_full_name()) or "",
            "gender": profile.gender if profile else None,
            "skin_type": (profile.skin_type if profile and profile.skin_type else None) or intake.get("skin_type"),
            "age": age,
            "concerns": intake.get("concerns") or [],
            "allergies": [],
            "additional_details": intake.get("additional_details"),
            "is_pregnant": False,
        }

    @database_sync_to_async
    def build_product_catalog(self):
        return build_product_catalog(self._base_url())

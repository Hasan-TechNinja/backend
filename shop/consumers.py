import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import ChatSession, ChatMessage
from product.models import Product
from account.models import Profile
from . import ai_engine

User = get_user_model()

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
        except Exception as e:
            import traceback
            traceback.print_exc()
            await self.close()
        
    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
            
        try:
            data = json.loads(text_data)
            message = data.get('message', '')
            image_b64 = data.get('image_b64', None)
            
            if not message and not image_b64:
                return
                
            # Get user profile and product catalog
            user_profile = await self.build_user_profile(self.user.id)
            product_catalog = await self.build_product_catalog()
            
            # Load chat history
            chat_history = await self.get_chat_history(self.session_id)
            summary_anchor = await self.get_summary_anchor(self.session_id)
            
            # Call AI Engine
            result = await ai_engine.chat_assistant(
                user_input=message,
                chat_history=chat_history,
                summary_anchor=summary_anchor,
                user_profile=user_profile,
                product_catalog=product_catalog,
                user_image_b64=image_b64
            )
            
            reply = result.get("response", "")
            updated_anchor = result.get("updated_summary_anchor", summary_anchor)
            is_for_friend = result.get("is_for_friend", False)
            
            # Save exchange
            await self.save_exchange(self.session_id, message, reply, is_for_friend, updated_anchor)
            
            # Send reply to client
            await self.send(text_data=json.dumps({
                'response': reply,
                'is_for_friend': is_for_friend
            }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Invalid JSON format. Expected an object like {'message': '...'}."}))
        except Exception as e:
            import traceback
            traceback.print_exc()
            await self.send(text_data=json.dumps({"error": f"Internal server error: {str(e)}"}))

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
        history = []
        for msg in messages:
            history.append({"role": msg.role, "content": msg.content})
        return history

    @database_sync_to_async
    def save_exchange(self, session_id, user_msg, assistant_msg, is_for_friend, updated_anchor):
        if user_msg:
            ChatMessage.objects.create(session_id=session_id, role='user', content=user_msg, is_for_friend=is_for_friend)
        if assistant_msg:
            ChatMessage.objects.create(session_id=session_id, role='assistant', content=assistant_msg, is_for_friend=is_for_friend)
        
        if not is_for_friend:
            session = ChatSession.objects.get(id=session_id)
            session.summary_anchor = updated_anchor
            session.save()

    @database_sync_to_async
    def build_user_profile(self, user_id):
        user = User.objects.get(id=user_id)
        profile = Profile.objects.filter(user_id=user_id).first()
        today = timezone.now()
        tenure = (today - user.date_joined).days if user.date_joined else 0
        
        if not profile:
            return {
                "language": "en",
                "full_name": user.get_full_name(),
                "account_tenure_days": tenure,
                "is_pregnant": False,
            }
            
        return {
            "language": getattr(profile, "language", "en") if hasattr(profile, 'language') else "en",
            "full_name": profile.full_name or user.get_full_name(),
            "gender": profile.gender,
            "age": 29, 
            "skin_type": profile.skin_type,
            "allergies": [],
            "climate": getattr(profile, "climate", ""),
            "sensitivity_level": getattr(profile, "sensitivity_level", "low") if hasattr(profile, 'sensitivity_level') else "low",
            "account_tenure_days": tenure,
            "is_pregnant": False, 
        }

    @database_sync_to_async
    def build_product_catalog(self):
        catalog = []
        # Filter only active/in-stock products as per DB definition
        products = Product.objects.all()
        for p in products:
            image_url = ""
            if p.images.exists() and p.images.first().image:
                image_url = p.images.first().image.url
                
            catalog.append({
                "id": p.id,
                "name": p.title,
                "name_ar": p.title,
                "type": p.category.name if p.category else "Skincare",
                "brand": getattr(p, "brand_name", "PureGlow"),
                "ingredients": p.key_ingredients or "",
                "benefits": p.key_benefits or "",
                "safety": "",
                "price": float(p.price) if p.price else 0.0,
                "image_url": image_url,
                "product_url": f"/product/{p.id}",
                "how_to_use": p.how_to_use or "",
            })
        return catalog

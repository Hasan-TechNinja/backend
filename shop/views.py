from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import re
from asgiref.sync import async_to_sync
from django.db import transaction
from .models import Cart, CartItem, Order, OrderItem, PaymentTransaction
from .serializers import (
    CartSerializer, CartItemSerializer, 
    OrderSerializer, CheckoutRequestSerializer,
    AIRoutineRequestSerializer
)
from .services import HyperPayService
from .tasks import sync_order_to_omniful
from django.conf import settings
from product.models import Product
from skincare.response import success_response
from . import ai_engine
class CartView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Show user's cart",
        operation_description="Get the current authenticated user's cart items and total price.",
        responses={200: CartSerializer},
        tags=['Shop']
    )
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart, context={'request': request})
        return success_response(
            message="Cart fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Add item to cart",
        operation_description="Add a product to the cart or increment quantity if already exists.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['product_id'],
            properties={
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, default=1),
            }
        ),
        responses={201: CartItemSerializer},
        tags=['Shop']
    )
    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id)

        # Check stock availability
        if product.stock < quantity:
            return Response(
                {"error": "Not enough stock available."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        
        cart_item.save()
        
        serializer = CartItemSerializer(cart_item, context={'request': request})
        return success_response(
            message="Item added to cart successfully",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_summary="Update cart item quantity",
        operation_description="Update the quantity of a specific item in the cart.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['quantity'],
            properties={
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        ),
        responses={200: CartItemSerializer},
        tags=['Shop']
    )
    def patch(self, request, item_id):
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        quantity = int(request.data.get('quantity', cart_item.quantity))
        
        if cart_item.product.stock < quantity:
            return Response(
                {"error": "Not enough stock available."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        cart_item.quantity = quantity
        cart_item.save()
        
        serializer = CartItemSerializer(cart_item, context={'request': request})
        return success_response(
            message="Cart item updated successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Remove item from cart",
        operation_description="Remove a specific item from the user's cart.",
        responses={200: openapi.Response(description="Item removed successfully")},
        tags=['Shop']
    )
    def delete(self, request, item_id):
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        
        return success_response(
            message="Item removed from cart successfully",
            data=None,
            status_code=status.HTTP_200_OK
        )


class InitiateCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Initiate Checkout",
        operation_description="Create a pending order and get HyperPay checkoutId.",
        request_body=CheckoutRequestSerializer,
        tags=['Checkout']
    )
    def post(self, request):
        serializer = CheckoutRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        cart = get_object_or_404(Cart, user=request.user)
        if not cart.items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        payment_brand = serializer.validated_data['payment_brand']
        
        # Access HYPERPAY_ENTITY_IDS from settings
        entity_ids = getattr(settings, 'HYPERPAY_ENTITY_IDS', {})
        entity_id = entity_ids.get(payment_brand)
        
        if not entity_id:
            return Response(
                {"error": f"Invalid payment brand or missing entityId for {payment_brand}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # Create Order
                order_data = {k: v for k, v in serializer.validated_data.items() if k != 'payment_brand'}
                order = Order.objects.create(
                    user=request.user,
                    total_amount=cart.total_price,
                    status='pending',
                    **order_data
                )
                
                # Create OrderItems
                for item in cart.items.all():
                    # Calculate price after discount
                    price = item.product.price
                    if item.product.discount > 0:
                        price = price - (price * item.product.discount / 100)
                    
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=price
                    )
                
                # Call HyperPay Service
                hyperpay = HyperPayService()
                hp_response = hyperpay.initiate_checkout(
                    amount=order.total_amount,
                    currency='SAR',
                    entity_id=entity_id,
                    user_details=serializer.validated_data
                )
                
                if not hp_response or 'id' not in hp_response:
                    # Log error and raise to rollback
                    error_msg = hp_response.get('result', {}).get('description', 'Unknown error') if hp_response else 'No response from HyperPay'
                    raise Exception(f"HyperPay initiation failed: {error_msg}")
                
                checkout_id = hp_response['id']
                
                # Create PaymentTransaction record
                PaymentTransaction.objects.create(
                    order=order,
                    checkout_id=checkout_id,
                    amount=order.total_amount,
                    currency='SAR',
                    payment_brand=payment_brand
                )
                
                return success_response(
                    message="Checkout initiated successfully",
                    data={
                        "checkoutId": checkout_id,
                        "orderId": order.id
                    },
                    status_code=status.HTTP_201_CREATED
                )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentCallbackView(APIView):
    """
    Endpoint to receive redirect from HyperPay and verify transaction status.
    """
    @swagger_auto_schema(
        operation_summary="Verify Payment Status",
        operation_description="Handle callback/redirect from HyperPay to verify the transaction.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['resourcePath'],
            properties={
                'resourcePath': openapi.Schema(type=openapi.TYPE_STRING, description="The path returned by HyperPay redirect"),
            }
        ),
        tags=['Checkout']
    )
    def post(self, request):
        resource_path = request.data.get('resourcePath')
        if not resource_path:
            return Response({"error": "resourcePath is required"}, status=status.HTTP_400_BAD_REQUEST)

        # resourcePath usually looks like /v1/checkouts/{id}/payment
        # We extract the checkout_id
        parts = resource_path.split('/')
        if len(parts) < 4:
            return Response({"error": "Invalid resourcePath"}, status=status.HTTP_400_BAD_REQUEST)
        
        checkout_id = parts[3]
        
        transaction_obj = get_object_or_404(PaymentTransaction, checkout_id=checkout_id)
        order = transaction_obj.order
        
        entity_ids = getattr(settings, 'HYPERPAY_ENTITY_IDS', {})
        entity_id = entity_ids.get(transaction_obj.payment_brand)
        
        hyperpay = HyperPayService()
        hp_status = hyperpay.get_payment_status(checkout_id, entity_id)
        
        if not hp_status:
            return Response({"error": "Failed to verify payment status with HyperPay"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Update transaction details
        transaction_obj.transaction_id = hp_status.get('id')
        transaction_obj.result_code = hp_status.get('result', {}).get('code')
        transaction_obj.result_description = hp_status.get('result', {}).get('description')
        transaction_obj.payload = hp_status
        transaction_obj.save()
        
        # Success codes pattern for HyperPay
        success_pattern = re.compile(r"^(000\.000\.|000\.100\.1|000\.[36]|000\.400\.[01]|000\.200\.)")
        
        if success_pattern.match(transaction_obj.result_code):
            with transaction.atomic():
                order.status = 'paid'
                order.save()
                
                # Clear User's Cart
                Cart.objects.filter(user=order.user).delete()
                
                # Trigger OMS Sync via Celery
                sync_order_to_omniful.delay(order.id)
            
            return success_response(
                message="Payment successful and order confirmed",
                data={
                    "orderId": order.id,
                    "status": "paid",
                    "transactionId": transaction_obj.transaction_id
                },
                status_code=status.HTTP_200_OK
            )
        else:
            order.status = 'failed'
            order.save()
            return Response({
                "error": "Payment validation failed",
                "message": transaction_obj.result_description,
                "code": transaction_obj.result_code
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

class GenerateAIRoutineView(APIView):
    @swagger_auto_schema(
        operation_summary="Generate AI Skin Routine",
        operation_description="Submit user skin profile to get an AI generated routine.",
        request_body=AIRoutineRequestSerializer,
        tags=['Shop']
    )
    def post(self, request):
        serializer = AIRoutineRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        user_profile = {
            "language": "en",
            "is_pregnant": False, 
            "skin_type": data.get("skin_type"),
            "concerns": data.get("concerns", []),
            "age": data.get("age"),
            "allergies": [], 
        }
        
        if data.get("additional_details"):
            user_profile["additional_details"] = data.get("additional_details")

        products = Product.objects.all()
        product_catalog = []
        for p in products:
            image_url = ""
            if p.images.exists() and p.images.first().image:
                image_url = request.build_absolute_uri(p.images.first().image.url)
            
            product_catalog.append({
                "id": p.id,
                "name": p.title,
                "name_ar": p.title,
                "type": p.category.name if p.category else "Skincare",
                "ingredients": p.key_ingredients or "",
                "benefits": p.key_benefits or "",
                "safety": "",
                "price": float(p.price) if p.price else 0.0,
                "image_url": image_url,
                "product_url": f"/product/{p.id}",
            })
            
        user_image_b64 = None
        photo = data.get("photo") or request.FILES.get("photo")
        if photo:
            import base64
            user_image_b64 = base64.b64encode(photo.read()).decode("utf-8")
            
        routine = async_to_sync(ai_engine.generate_routine)(
            user_profile, 
            product_catalog,
            user_image_b64=user_image_b64
        )

        # Enrich routine output to match frontend UI requirements
        for phase in ["am_routine", "pm_routine"]:
            for step in routine.get(phase, []):
                pid = step.get("product_id")
                if pid:
                    db_prod = Product.objects.filter(id=pid).first()
                    if db_prod:
                        brand = "PureGlow"
                        category = db_prod.category.name if db_prod.category else "Skincare"
                        
                        step["brand"] = brand
                        step["category"] = category
                        step["brand_type"] = db_prod.sub_title if db_prod.sub_title else f"{brand} • {category}"
                        step["how_to_use"] = db_prod.how_to_use if db_prod.how_to_use else step.get("rationale", "")
        
        from .models import GeneratedRoutine
        if request.user and request.user.is_authenticated:
            GeneratedRoutine.objects.create(
                user=request.user,
                skin_profile=user_profile,
                routine_data=routine
            )

        return success_response(
            message="Routine generated successfully",
            data=routine,
            status_code=status.HTTP_200_OK
        )

class RoutineHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get user's AI routine history",
        operation_description="Returns all previously generated AI skincare routines for the authenticated user.",
        tags=['Shop']
    )
    def get(self, request):
        from .models import GeneratedRoutine
        routines = GeneratedRoutine.objects.filter(user=request.user).order_by('-created_at')
        
        history = []
        for routine in routines:
            history.append({
                "id": routine.id,
                "skin_profile": routine.skin_profile,
                "routine_data": routine.routine_data,
                "created_at": routine.created_at.isoformat()
            })
            
        return success_response(
            message="Routine history retrieved successfully",
            data={"routines": history},
            status_code=status.HTTP_200_OK
        )


class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .models import ChatSession, ChatMessage
        session = ChatSession.objects.filter(user=request.user).first()
        if not session:
            return success_response(
                message="No chat history found",
                data={"messages": []},
                status_code=status.HTTP_200_OK
            )
            
        messages = ChatMessage.objects.filter(session=session).order_by('created_at')
        
        history = []
        for msg in messages:
            history.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "is_for_friend": msg.is_for_friend,
                "created_at": msg.created_at.isoformat()
            })
            
        return success_response(
            message="Chat history retrieved successfully",
            data={"messages": history},
            status_code=status.HTTP_200_OK
        )

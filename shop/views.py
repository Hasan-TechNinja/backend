from rest_framework import status
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import re
from asgiref.sync import async_to_sync
from django.db import transaction
from .models import Cart, CartItem, Order, OrderItem, PaymentTransaction, ChatSession, ChatMessage, GeneratedRoutine
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
from .catalog import build_product_catalog, get_catalog_product
from PIL import Image
import io
import base64
def queue_order_sync(order_id):
    """Push the order to the OMS after commit; never let a broker outage break checkout."""
    def _send():
        try:
            sync_order_to_omniful.apply_async(args=[order_id], retry=False, ignore_result=True)
        except Exception as e:
            logging.error(f"Could not queue Omniful sync for order {order_id}: {e}")
    transaction.on_commit(_send)


def fulfil_order_stock(order):
    """Decrement stock and bump best-seller counters for every item in the order."""
    for item in order.items.all():
        product = Product.objects.select_for_update().get(id=item.product_id)
        product.stock = max(0, product.stock - item.quantity)
        product.order_count += item.quantity
        product.save(update_fields=['stock', 'order_count'])


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
        try:
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response({"error": "Quantity must be a number."}, status=status.HTTP_400_BAD_REQUEST)
        if quantity < 1:
            return Response({"error": "Quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)

        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        new_quantity = quantity + (cart_item.quantity if cart_item else 0)

        # Check stock availability against the total quantity in the cart
        if product.stock < new_quantity:
            return Response(
                {"error": f"Only {product.stock} left in stock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if cart_item:
            cart_item.quantity = new_quantity
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(cart=cart, product=product, quantity=quantity)
        
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
        
        try:
            quantity = int(request.data.get('quantity', cart_item.quantity))
        except (TypeError, ValueError):
            return Response({"error": "Quantity must be a number."}, status=status.HTTP_400_BAD_REQUEST)
        if quantity < 1:
            return Response({"error": "Quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)

        if cart_item.product.stock < quantity:
            return Response(
                {"error": f"Only {cart_item.product.stock} left in stock."},
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

        for item in cart.items.select_related('product'):
            if item.product.stock < item.quantity:
                return Response(
                    {"error": f"Only {item.product.stock} of {item.product.title} left in stock. Please update your cart."},
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
                
                if payment_brand == 'COD':
                    # Cash on Delivery: the order is confirmed straight away
                    fulfil_order_stock(order)
                    Cart.objects.filter(user=request.user).delete()
                    queue_order_sync(order.id)
                    
                    return success_response(
                        message="Order placed successfully with Cash on Delivery",
                        data={"orderId": order.id, "status": "pending"},
                        status_code=status.HTTP_201_CREATED
                    )

                # Access HYPERPAY_ENTITY_IDS from settings
                entity_ids = getattr(settings, 'HYPERPAY_ENTITY_IDS', {})
                entity_id = entity_ids.get(payment_brand)
                
                if not entity_id:
                    raise Exception(f"Invalid payment brand or missing entityId for {payment_brand}")
                
                # Call HyperPay Service
                hyperpay = HyperPayService()
                name_parts = serializer.validated_data['full_name'].split(maxsplit=1)
                hp_response = hyperpay.initiate_checkout(
                    amount=order.total_amount,
                    currency='SAR',
                    entity_id=entity_id,
                    user_details={
                        **serializer.validated_data,
                        'email': request.user.email,
                        'first_name': name_parts[0],
                        'last_name': name_parts[1] if len(name_parts) > 1 else name_parts[0],
                    }
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
            logging.exception("Checkout failed")
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
        
        if success_pattern.match(transaction_obj.result_code or ''):
            with transaction.atomic():
                # The gateway may redirect more than once; only fulfil the order the first time
                if order.status != 'paid':
                    order.status = 'paid'
                    order.save()
                    fulfil_order_stock(order)
                    Cart.objects.filter(user=order.user).delete()
                    queue_order_sync(order.id)
            
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


class OrderDeliveredView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Update Order Status to Delivered",
        operation_description="User can mark their Cash on Delivery order as delivered.",
        tags=['Shop']
    )
    def patch(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        if order.status == 'delivered':
            return Response({"error": "Order is already delivered"}, status=status.HTTP_400_BAD_REQUEST)
            
        order.status = 'delivered'
        order.save()
        
        return success_response(
            message="Order status updated to delivered successfully",
            data={"orderId": order.id, "status": "delivered"},
            status_code=status.HTTP_200_OK
        )


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get user's order list",
        operation_description="Returns a list of all orders placed by the authenticated user.",
        responses={200: OrderSerializer(many=True)},
        tags=['Shop']
    )
    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True, context={"request": request})
        return success_response(
            message="Order list fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

class GenerateAIRoutineView(APIView):
    permission_classes = [AllowAny]
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
        language = 'ar' if (data.get("language") or "").lower().startswith("ar") else 'en'

        user_profile = {
            "language": language,
            "is_pregnant": False,
            "skin_type": data.get("skin_type"),
            "concerns": data.get("concerns", []),
            "age": data.get("age"),
            "allergies": [],
        }
        if data.get("additional_details"):
            user_profile["additional_details"] = data.get("additional_details")

        # Use the chat memory too when the user is signed in
        chat_history = []
        summary_anchor = ""
        if request.user.is_authenticated:
            session = ChatSession.objects.filter(user=request.user).first()
            if session:
                summary_anchor = session.summary_anchor
                messages = ChatMessage.objects.filter(session=session).order_by('-created_at')[:10]
                chat_history = [{"role": msg.role, "content": msg.content} for msg in reversed(messages)]

        pil_image = None
        photo = data.get("photo") or request.FILES.get("photo")
        if photo:
            try:
                pil_image = Image.open(photo)
            except Exception as e:
                logging.error(f"Image open error: {e}")

        base_url = request.build_absolute_uri("/").rstrip("/")
        product_catalog = build_product_catalog(base_url)

        routine_obj = async_to_sync(ai_engine.generate_routine)(
            user_profile=user_profile,
            product_catalog=product_catalog,
            chat_history=chat_history,
            summary_anchor=summary_anchor,
            image=pil_image,
            language=language,
        )

        if not routine_obj:
            return Response(
                {"error": "We couldn't prepare your routine right now. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        routine = {
            "am_routine": [s.model_dump() for s in routine_obj.morning_routine],
            "pm_routine": [s.model_dump() for s in routine_obj.evening_routine],
            "reasoning": routine_obj.reasoning
        }

        # Enrich each step with live product data
        for phase in ["am_routine", "pm_routine"]:
            for step in routine[phase]:
                product = get_catalog_product(product_catalog, step.get("product_id"))
                if not product:
                    continue
                step["product_name"] = product["name"]
                step["brand"] = "Glowmi"
                step["category"] = product["category"]
                step["brand_type"] = product["sub_title"] or f"Glowmi • {product['category']}"
                step["how_to_use"] = step.get("usage_instructions") or product["how_to_use"]
                step["image_url"] = product["image_url"]
                step["product_url"] = product["product_url"]
                step["price"] = product["price"]

        GeneratedRoutine.objects.create(
            user=request.user if request.user.is_authenticated else None,
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
    
    @swagger_auto_schema(
        operation_summary="Delete AI routine",
        operation_description="Deletes a specific AI generated routine for the authenticated user.",
        tags=['Shop']
    )
    def delete(self, request, routine_id):
        from .models import GeneratedRoutine
        routine = GeneratedRoutine.objects.filter(user=request.user, id=routine_id).first()
        if not routine:
            return success_response(
                message="Routine not found",
                data={},
                status_code=status.HTTP_404_NOT_FOUND
            )
        routine.delete()
        return success_response(
            message="Routine deleted successfully",
            data={},
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

from django.urls import path
from .views import CartView, InitiateCheckoutView, PaymentCallbackView, GenerateAIRoutineView, RoutineHistoryView, ChatHistoryView, OrderDeliveredView, OrderListView

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart-detail'),
    path('cart/items/<int:item_id>/', CartView.as_view(), name='cart-item-detail'),
    
    # Checkout & Payment
    path('checkout/initiate/', InitiateCheckoutView.as_view(), name='checkout-initiate'),
    path('checkout/verify/', PaymentCallbackView.as_view(), name='checkout-verify'),
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('order/<int:order_id>/delivered/', OrderDeliveredView.as_view(), name='order-delivered'),
    
    # AI Routine & Chat
    path('generate-routine/', GenerateAIRoutineView.as_view(), name='generate-routine'),
    path('routine/history/', RoutineHistoryView.as_view(), name='routine-history'),
    path('chat/history/', ChatHistoryView.as_view(), name='chat-history'),
]
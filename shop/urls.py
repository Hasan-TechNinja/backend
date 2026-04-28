from django.urls import path
from .views import CartView, InitiateCheckoutView, PaymentCallbackView

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart-detail'),
    path('cart/items/<int:item_id>/', CartView.as_view(), name='cart-item-detail'),
    
    # Checkout & Payment
    path('checkout/initiate/', InitiateCheckoutView.as_view(), name='checkout-initiate'),
    path('checkout/verify/', PaymentCallbackView.as_view(), name='checkout-verify'),
]
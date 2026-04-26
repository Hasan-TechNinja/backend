from django.urls import path
from .views import CartView

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart-detail'),
    path('cart/items/<int:item_id>/', CartView.as_view(), name='cart-item-detail'),
]
 
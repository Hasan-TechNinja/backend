from django.contrib import admin
from . models import CartItem


class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'subtotal')
    list_filter = ('cart', 'product')
    search_fields = ('cart', 'product')
    ordering = ('-id',)
    

admin.site.register(CartItem, CartItemAdmin)
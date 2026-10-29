from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from product.models import Product
from product.serializers import ProductListserializer

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListserializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'subtotal']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def to_representation(self, instance):
        # product_id is write-only for input; the frontend also needs it to match cart rows
        data = super().to_representation(instance)
        data['product_id'] = instance.product_id
        return data


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.title')
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'quantity', 'price']

    def get_product_image(self, obj):
        image = obj.product.images.first()
        if not image or not image.image:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(image.image.url) if request else image.image.url

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'total_amount', 'status', 'items',
            'full_name', 'phone',
            'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country', 'created_at'
        ]
        read_only_fields = ['user', 'total_amount', 'status']

class CheckoutRequestSerializer(serializers.Serializer):
    payment_brand = serializers.ChoiceField(choices=['VISA', 'MASTER', 'MADA', 'APPLEPAY', 'TABBY', 'TAMARA', 'COD'])
    full_name = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=20)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=100, default='SA')

class AIRoutineRequestSerializer(serializers.Serializer):
    skin_type = serializers.CharField(max_length=50)
    age = serializers.IntegerField()
    concerns = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False
    )
    additional_details = serializers.CharField(required=False, allow_blank=True)
    photo = serializers.ImageField(required=False, allow_null=True)
    language = serializers.CharField(max_length=5, required=False, allow_blank=True)


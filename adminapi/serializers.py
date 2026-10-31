from rest_framework import serializers
from account.models import User, Profile, PrivacyPolicy, TermsAndConditions
from django.db.models import Sum
from category.serializers import Categorylistserializer
from shop.models import GeneratedRoutine, Order, OrderItem

# Orders in these states never became a sale
NON_SALE_STATUSES = ['cancelled', 'failed']

class UserListSerializer(serializers.ModelSerializer):
    membership_id = serializers.SerializerMethodField()
    name = serializers.CharField(source='profile.full_name', read_only=True)
    contact_number = serializers.CharField(source='profile.contact_number', read_only=True)
    skin_type = serializers.CharField(source='profile.skin_type', read_only=True)
    birth_date = serializers.DateField(source='profile.date_of_birth', read_only=True, format="%d/%m/%Y")
    join_date = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = ['membership_id', 'name', 'email', 'role', 'contact_number', 'skin_type', 'birth_date', 'join_date']

    def get_membership_id(self, obj):
        return obj.username


class PrivacyPolicyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = ['id', 'title', 'content', 'created_at', 'updated_at']


class TermsAndConditionsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsAndConditions
        fields = ['id', 'title', 'content', 'created_at', 'updated_at']


class CustomerListSerializer(serializers.ModelSerializer):
    membership_id = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source='profile.full_name', read_only=True)
    orders = serializers.IntegerField(source='orders_count', read_only=True)
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    location = serializers.SerializerMethodField()
    id_format = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'membership_id', 'id_format', 'customer_name', 'location', 'orders', 'total_spent', 'phone_number']

    def get_membership_id(self, obj):
        return obj.username

    def get_id_format(self, obj):
        return f"#{obj.username}" if obj.username else f"#{obj.id}"

    def get_location(self, obj):
        latest_order = obj.orders.order_by('-created_at').first()
        if latest_order:
            parts = [p for p in [latest_order.address_line1, latest_order.city, latest_order.state, latest_order.postal_code] if p]
            return ", ".join(parts)
        return ""

    def get_phone_number(self, obj):
        if hasattr(obj, 'profile') and obj.profile and obj.profile.contact_number:
            return obj.profile.contact_number
        latest_order = obj.orders.order_by('-created_at').first()
        if latest_order and latest_order.phone:
            return latest_order.phone
        return ""


class UserDetailSerializer(serializers.ModelSerializer):
    membership_id = serializers.SerializerMethodField()
    name = serializers.CharField(source='profile.full_name', read_only=True)
    contact_number = serializers.CharField(source='profile.contact_number', read_only=True)
    skin_type = serializers.CharField(source='profile.skin_type', read_only=True)
    birth_date = serializers.DateField(source='profile.date_of_birth', read_only=True, format="%d/%m/%Y")
    gender = serializers.CharField(source='profile.gender', read_only=True)
    image = serializers.ImageField(source='profile.image', read_only=True)
    address = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()
    join_date = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'membership_id', 'email', 'role', 'is_active', 'name', 'contact_number', 'skin_type', 'birth_date', 'gender', 'image', 'address', 'order_count', 'total_spent', 'orders', 'join_date']

    def get_membership_id(self, obj):
        return obj.username

    def get_address(self, obj):
        latest_order = obj.orders.order_by('-created_at').first()
        if latest_order:
            parts = [p for p in [latest_order.address_line1, latest_order.city, latest_order.state, latest_order.postal_code] if p]
            return ", ".join(parts)
        return ""

    def get_order_count(self, obj):
        return obj.orders.count()

    def get_total_spent(self, obj):
        return obj.orders.exclude(status__in=NON_SALE_STATUSES).aggregate(total=Sum('total_amount'))['total'] or 0

    def get_orders(self, obj):
        orders = obj.orders.prefetch_related('items__product__images').order_by('-created_at')[:20]
        return OrderListSerializer(orders, many=True, context=self.context).data


class AnalyserListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name', read_only=True)
    join_date = serializers.DateTimeField(source='date_joined', read_only=True)
    active_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'join_date', 'active_status']

    def get_active_status(self, obj):
        return "active" if obj.is_active else "inactive"


class GeneratedRoutineSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedRoutine
        fields = ['id', 'skin_profile', 'routine_data', 'created_at']


class AnalyserDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name', read_only=True)
    image = serializers.ImageField(source='profile.image', read_only=True)
    join_date = serializers.DateTimeField(source='date_joined', read_only=True)
    active_status = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()
    routines = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'image', 'join_date', 'active_status', 'location', 'order_count', 'routines']

    def get_active_status(self, obj):
        return "active" if obj.is_active else "inactive"

    def get_location(self, obj):
        latest_order = obj.orders.order_by('-created_at').first()
        return latest_order.city if latest_order else ""

    def get_order_count(self, obj):
        return obj.orders.count()

    def get_routines(self, obj):
        return GeneratedRoutineSerializer(obj.routines.order_by('-created_at'), many=True).data


class AdminCategorySerializer(Categorylistserializer):
    """Adds the stock and sales columns shown on the dashboard category table."""
    product_count = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    sale = serializers.SerializerMethodField()

    class Meta(Categorylistserializer.Meta):
        fields = Categorylistserializer.Meta.fields + ['product_count', 'quantity', 'sale']

    def get_product_count(self, obj):
        return getattr(obj, 'product_count', 0) or 0

    def get_quantity(self, obj):
        return getattr(obj, 'quantity', 0) or 0

    def get_sale(self, obj):
        return getattr(obj, 'sale', 0) or 0


class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name', required=False, allow_null=True, allow_blank=True)
    contact_number = serializers.CharField(source='profile.contact_number', required=False, allow_null=True, allow_blank=True)
    skin_type = serializers.CharField(source='profile.skin_type', required=False, allow_null=True, allow_blank=True)
    birth_date = serializers.DateField(source='profile.date_of_birth', required=False, allow_null=True)
    gender = serializers.CharField(source='profile.gender', required=False, allow_null=True, allow_blank=True)
    image = serializers.ImageField(source='profile.image', required=False, allow_null=True)
    join_date = serializers.DateTimeField(source='date_joined', read_only=True)
    
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    membership_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'membership_id', 'email', 'full_name', 'role', 
            'contact_number', 'skin_type', 'birth_date', 'gender', 'image',
            'password', 'confirm_password', 'is_active', 'join_date'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'role': {'required': True},
        }

    def get_membership_id(self, obj):
        return obj.username

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        # Check if it's a create operation
        if not self.instance:
            if not password:
                raise serializers.ValidationError({"password": "Password is required for new users."})
            if not confirm_password:
                raise serializers.ValidationError({"confirm_password": "Confirm password is required."})

        if password or confirm_password:
            if password != confirm_password:
                raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
            
            from django.contrib.auth import password_validation
            try:
                password_validation.validate_password(password)
            except Exception as e:
                raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password')
        validated_data.pop('confirm_password', None)

        user = User.objects.create_user(
            email=validated_data['email'],
            username=User().generate_unique_username(),
            password=password,
            role=validated_data['role'],
            is_active=True 
        )

        # Create or update profile
        from account.models import Profile
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Update profile with all provided fields
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.save()
        
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)

        # Update User fields
        instance.email = validated_data.get('email', instance.email)
        instance.role = validated_data.get('role', instance.role)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        
        if password:
            instance.set_password(password)
        
        instance.save()

        # Update Profile fields
        from account.models import Profile
        profile, created = Profile.objects.get_or_create(user=instance)
        
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.save()
        instance.profile = profile

        return instance


# Orders

def get_payment_status(order):
    if order.status in NON_SALE_STATUSES:
        return order.status
    # Card payments are confirmed by the gateway; cash on delivery is collected on delivery
    is_prepaid = getattr(order, 'payment_transaction', None) is not None
    paid_statuses = ['paid', 'shipped', 'delivered'] if is_prepaid else ['paid', 'delivered']
    return 'paid' if order.status in paid_statuses else 'pending'


def get_payment_method(order):
    transaction = getattr(order, 'payment_transaction', None)
    return transaction.payment_brand if transaction else 'COD'


class OrderItemForAdminSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.title', read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'quantity', 'price']

    def get_product_image(self, obj):
        request = self.context.get('request')
        first_image = obj.product.images.first()
        if first_image and first_image.image:
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None


class OrderListSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_membership = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()
    items = OrderItemForAdminSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_email', 'user_membership', 'total_amount', 'status',
            'payment_status', 'payment_method',
            'full_name', 'phone', 'address_line1', 'address_line2', 'city', 'state', 'postal_code',
            'country', 'created_at', 'updated_at', 'items'
        ]

    def get_user_membership(self, obj):
        return obj.user.username

    def get_payment_status(self, obj):
        return get_payment_status(obj)

    def get_payment_method(self, obj):
        return get_payment_method(obj)


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)

    def validate_status(self, value):
        # Normalize to lower-case stored values
        return value
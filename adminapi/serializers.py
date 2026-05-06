from rest_framework import serializers
from account.models import User, Profile, PrivacyPolicy, TermsAndConditions
from django.db.models import Sum
# from order.models import Order  

class UserListSerializer(serializers.ModelSerializer):
    membership_id = serializers.SerializerMethodField()
    name = serializers.CharField(source='profile.full_name', read_only=True)
    contact_number = serializers.CharField(source='profile.contact_number', read_only=True)
    skin_type = serializers.CharField(source='profile.skin_type', read_only=True)
    birth_date = serializers.DateField(source='profile.date_of_birth', read_only=True, format="%d/%m/%Y")

    class Meta:
        model = User
        fields = ['membership_id', 'name', 'email', 'contact_number', 'skin_type', 'birth_date']

    def get_membership_id(self, obj):
        return f"G{obj.id:04d}"


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
        return f"G{obj.id:04d}"

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
    address = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'membership_id', 'email', 'name', 'contact_number', 'skin_type', 'birth_date', 'address', 'order_count', 'total_spent']

    def get_membership_id(self, obj):
        return f"G{obj.id:04d}"

    def get_address(self, obj):
        latest_order = obj.orders.order_by('-created_at').first()
        if latest_order:
            parts = [p for p in [latest_order.address_line1, latest_order.city, latest_order.state, latest_order.postal_code] if p]
            return ", ".join(parts)
        return ""

    def get_order_count(self, obj):
        return obj.orders.count()

    def get_total_spent(self, obj):
        return obj.orders.aggregate(total=Sum('total_amount'))['total'] or 0    


class AnalyserListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name', read_only=True)
    join_date = serializers.DateTimeField(source='date_joined', read_only=True)
    active_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'join_date', 'active_status']

    def get_active_status(self, obj):
        return "active" if obj.is_active else "inactive"


class AnalyserDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name', read_only=True)
    join_date = serializers.DateTimeField(source='date_joined', read_only=True)
    active_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'join_date', 'active_status']

    def get_active_status(self, obj):
        return "active" if obj.is_active else "inactive"
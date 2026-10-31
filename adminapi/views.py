from django.http import Http404
from rest_framework import generics
from account.models import User, PrivacyPolicy, TermsAndConditions
from .serializers import (
    UserListSerializer, PrivacyPolicyListSerializer, TermsAndConditionsListSerializer,
    CustomerListSerializer, UserDetailSerializer, AnalyserListSerializer,
    AnalyserDetailSerializer, AdminUserSerializer, AdminCategorySerializer,
    NON_SALE_STATUSES, get_payment_status
)
from account import permissions
from category.models import Category
from category.serializers import Categorylistserializer
from skincare.pagination import AdminPagination
from skincare.response import success_response
from rest_framework import status
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce, ExtractMonth
from shop.models import GeneratedRoutine
from product.models import Product
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from shop.models import Order
from .serializers import OrderListSerializer
import calendar
import json

# Orders that count as revenue
REVENUE_STATUSES = ['paid', 'shipped', 'delivered']


def percent_change(current, previous):
    if not previous:
        return 100.0 if current else 0.0
    return round((current - previous) / previous * 100, 2)


def get_routine_steps(routine):
    """All morning and evening steps of a generated routine, tolerating malformed data."""
    data = routine.routine_data
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return []
    if not isinstance(data, dict):
        return []

    steps = []
    for key in ('am_routine', 'pm_routine'):
        phase = data.get(key)
        if isinstance(phase, list):
            steps.extend(step for step in phase if isinstance(step, dict))
    return steps


def block_self_delete(request, user):
    if user.pk == request.user.pk:
        return Response({"error": "You can't delete your own account."}, status=status.HTTP_400_BAD_REQUEST)
    return None

# Create your views here.

class UserListCreateApiView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAdminRole]
    pagination_class = AdminPagination
    search_fields = ['username', 'email', 'profile__full_name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminUserSerializer
        return UserListSerializer

    def get_queryset(self):
        # Return both users and admins as the admin can now create both
        return User.objects.filter(role__in=['user', 'admin']).select_related('profile').order_by('-id')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(
            message="User created successfully",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )

class UserDeleteApiView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAdminRole]
    queryset = User.objects.filter(role__in=['user', 'admin'])

    def get_object(self):
        membership_id = self.kwargs.get('membership_id')
        if membership_id:
            try:
                return User.objects.filter(role__in=['user', 'admin']).get(username=membership_id)
            except User.DoesNotExist:
                if membership_id.startswith('G'):
                    try:
                        user_id = int(membership_id[1:])
                        return User.objects.filter(role__in=['user', 'admin']).get(id=user_id)
                    except (ValueError, User.DoesNotExist):
                        raise Http404
                else:
                    try:
                        return User.objects.filter(role__in=['user', 'admin']).get(pk=membership_id)
                    except (ValueError, User.DoesNotExist):
                        raise Http404
        return super().get_object()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        blocked = block_self_delete(request, instance)
        if blocked:
            return blocked
        self.perform_destroy(instance)
        return success_response(
            message="User deleted successfully",
            data=None,
            status_code=status.HTTP_200_OK
        )



class CategoryListCreateApiView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAdminRole]
    serializer_class = AdminCategorySerializer
    pagination_class = AdminPagination
    search_fields = ['name']
    queryset = Category.objects.annotate(
        product_count=Count('products'),
        quantity=Sum('products__stock'),
        sale=Sum('products__order_count'),
    ).order_by('-id')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(
            message="Category created successfully",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )


class PrivacyPolicyListCreateApiView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAdminRole]
    serializer_class = PrivacyPolicyListSerializer
    queryset = PrivacyPolicy.objects.all().order_by('-id')

    def create(self, request, *args, **kwargs):
        instance = PrivacyPolicy.objects.first()
        if instance:
            serializer = self.get_serializer(instance, data=request.data)
            message = "Privacy Policy updated successfully"
            status_code = status.HTTP_200_OK
        else:
            serializer = self.get_serializer(data=request.data)
            message = "Privacy Policy created successfully"
            status_code = status.HTTP_201_CREATED

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            message=message,
            data=serializer.data,
            status_code=status_code
        )


class TermsAndConditionsListCreateApiView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAdminRole]
    serializer_class = TermsAndConditionsListSerializer
    queryset = TermsAndConditions.objects.all().order_by('-id')

    def create(self, request, *args, **kwargs):
        instance = TermsAndConditions.objects.first()
        if instance:
            serializer = self.get_serializer(instance, data=request.data)
            message = "Terms and Conditions updated successfully"
            status_code = status.HTTP_200_OK
        else:
            serializer = self.get_serializer(data=request.data)
            message = "Terms and Conditions created successfully"
            status_code = status.HTTP_201_CREATED

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            message=message,
            data=serializer.data,
            status_code=status_code
        )


class CustomerListApiView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminRole]
    serializer_class = CustomerListSerializer
    pagination_class = AdminPagination
    search_fields = ['username', 'email', 'profile__full_name']

    def get_queryset(self):
        customers = User.objects.filter(role='user').select_related('profile').annotate(
            orders_count=Count('orders', distinct=True),
            total_spent=Coalesce(
                Sum('orders__total_amount', filter=~Q(orders__status__in=NON_SALE_STATUSES)),
                Value(0),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
        )
        sort = self.request.query_params.get('sort')
        if sort == 'high-orders':
            return customers.order_by('-orders_count', '-id')
        if sort == 'low-orders':
            return customers.order_by('orders_count', '-id')
        return customers.order_by('-id')


class UserDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAdminRole]
    queryset = User.objects.all().select_related('profile')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AdminUserSerializer
        return UserDetailSerializer
    
    def get_object(self):
        membership_id = self.kwargs.get('membership_id')
        if membership_id:
            try:
                return User.objects.select_related('profile').get(username=membership_id)
            except User.DoesNotExist:
                if membership_id.startswith('G'):
                    try:
                        user_id = int(membership_id[1:])
                        return User.objects.select_related('profile').get(id=user_id)
                    except (ValueError, User.DoesNotExist):
                        raise Http404
                else:
                    # Fallback to PK if it's not a G-formatted ID
                    try:
                        return User.objects.select_related('profile').get(pk=membership_id)
                    except (ValueError, User.DoesNotExist):
                        raise Http404
        return super().get_object()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(
            message="User updated successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        blocked = block_self_delete(request, instance)
        if blocked:
            return blocked
        self.perform_destroy(instance)
        return success_response(
            message="User deleted successfully",
            data=None,
            status_code=status.HTTP_200_OK
        )


class AnalyserListApiView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminRole]
    serializer_class = AnalyserListSerializer
    pagination_class = AdminPagination
    search_fields = ['email', 'profile__full_name']

    def get_queryset(self):
        users = User.objects.filter(routines__isnull=False).select_related('profile').distinct().order_by('-id')
        active_status = self.request.query_params.get('status')
        if active_status in ('active', 'inactive'):
            users = users.filter(is_active=active_status == 'active')
        return users


class AnalyserDetailApiView(generics.RetrieveDestroyAPIView):
    permission_classes = [permissions.IsAdminRole]
    serializer_class = AnalyserDetailSerializer
    queryset = User.objects.all()
    lookup_field = 'pk'

    def get_object(self):
        return User.objects.filter(routines__isnull=False).distinct().get(pk=self.kwargs['pk'])

    def delete(self, request, *args, **kwargs):
        # Clears the skin analyses only; the user's account and orders stay
        self.get_object().routines.all().delete()
        return success_response(
            message="Skin analyses deleted successfully",
            data=None,
            status_code=status.HTTP_200_OK
        )


class AIAnalyticsProductListView(APIView):
    permission_classes = [permissions.IsAdminRole]

    def get(self, request):
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        routines_current = GeneratedRoutine.objects.filter(created_at__gte=thirty_days_ago)
        routines_previous = GeneratedRoutine.objects.filter(created_at__gte=sixty_days_ago, created_at__lt=thirty_days_ago)
        routines_all = GeneratedRoutine.objects.all()

        def count_products(routines):
            counts = {}
            for r in routines:
                for step in get_routine_steps(r):
                    pid = step.get('product_id')
                    if pid is not None:
                        try:
                            pid_int = int(pid)
                            counts[pid_int] = counts.get(pid_int, 0) + 1
                        except (ValueError, TypeError):
                            continue
            return counts

        current_counts = count_products(routines_current)
        previous_counts = count_products(routines_previous)
        all_counts = count_products(routines_all)

        # Fetch products that have at least one recommendation
        # Convert keys to list of ints for strict DB compatibility
        recommended_pids = list(all_counts.keys())

        if not recommended_pids:
            return success_response(
                message="No AI Analytics data available yet",
                data={"products": [], "performance_by_category": []},
                status_code=status.HTTP_200_OK
            )

        products = Product.objects.select_related('category').prefetch_related('images').filter(id__in=recommended_pids)

        result = []
        category_performance = {}

        for p in products:
            # Use int key for lookup since we converted all_counts keys to int
            total_recs = all_counts.get(p.id, 0)
            cur = current_counts.get(p.id, 0)
            prev = previous_counts.get(p.id, 0)

            # Category performance grouping
            cat_name = p.category.name if p.category else "Uncategorized"
            if cat_name not in category_performance:
                category_performance[cat_name] = {"current": 0, "previous": 0}

            category_performance[cat_name]["current"] += cur
            category_performance[cat_name]["previous"] += prev

            # Calculate trend
            if prev == 0:
                trend_val = 100.0 if cur > 0 else 0.0
            else:
                trend_val = ((cur - prev) / prev) * 100

            trend_str = f"+{trend_val:.1f}%" if trend_val > 0 else f"{trend_val:.1f}%"
            if trend_val == 0:
                trend_str = "0.0%"

            # Extract 'Top for' info from key_benefits or sub_title
            top_for = p.key_benefits if p.key_benefits else ""
            if len(top_for) > 60:
                top_for = top_for[:57] + "..."

            # Get first image URL
            image_url = ""
            first_image = p.images.first()
            if first_image and first_image.image:
                image_url = request.build_absolute_uri(first_image.image.url)

            result.append({
                "id": p.id,
                "product_name": p.title,
                "sub_title": p.sub_title,
                "category": cat_name,
                "recommendations": total_recs,
                "trend": trend_str,
                "top_for": top_for,
                "image": image_url
            })

        # Sort by total recommendations descending
        result.sort(key=lambda x: x['recommendations'], reverse=True)

        performance_list = [
            {"category": cat, "current": c_counts["current"], "previous": c_counts["previous"]}
            for cat, c_counts in category_performance.items()
        ]

        response_data = {
            "products": result,
            "performance_by_category": performance_list
        }

        return success_response(
            message="AI Analytics Products",
            data=response_data,
            status_code=status.HTTP_200_OK
        )


class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAdminRole]

    @staticmethod
    def _sale_chart(request, today):
        """Revenue per month (this year vs last year) or per day (last N days vs the N before)."""
        sales = Order.objects.filter(status__in=REVENUE_STATUSES)
        period = request.query_params.get('range', 'year')

        if period in ('7', '30'):
            days = int(period)
            start = today - timedelta(days=days - 1)
            previous_start = start - timedelta(days=days)
            daily = sales.filter(created_at__date__gte=previous_start).values('created_at__date').annotate(total=Sum('total_amount'))
            totals = {item['created_at__date']: float(item['total'] or 0) for item in daily}
            return {
                "year": today.year,
                "range": period,
                "points": [
                    {
                        "month": (start + timedelta(days=i)).strftime("%b %d"),
                        "thisMonth": round(totals.get(start + timedelta(days=i), 0.0), 2),
                        "lastMonth": round(totals.get(previous_start + timedelta(days=i), 0.0), 2),
                    }
                    for i in range(days)
                ],
            }

        try:
            year = int(request.query_params.get('year', today.year))
        except ValueError:
            year = today.year

        def monthly(for_year):
            rows = sales.filter(created_at__year=for_year).annotate(month=ExtractMonth('created_at')).values('month').annotate(total=Sum('total_amount'))
            return {item['month']: float(item['total'] or 0) for item in rows}

        this_year = monthly(year)
        last_year = monthly(year - 1)
        return {
            "year": year,
            "range": "year",
            "points": [
                {
                    "month": calendar.month_abbr[i],
                    "thisMonth": round(this_year.get(i, 0.0), 2),
                    "lastMonth": round(last_year.get(i, 0.0), 2),
                }
                for i in range(1, 13)
            ],
        }

    @staticmethod
    def _weekly_chart(queryset, date_field, today):
        """Daily counts for the last 7 days against the 7 days before."""
        start = today - timedelta(days=6)
        previous_start = start - timedelta(days=7)
        lookup = f'{date_field}__date'
        rows = queryset.filter(**{f'{lookup}__gte': previous_start}).values(lookup).annotate(count=Count('id'))
        counts = {item[lookup]: item['count'] for item in rows}

        points = [
            {
                "day": i + 1,
                "thisWeek": counts.get(start + timedelta(days=i), 0),
                "lastWeek": counts.get(previous_start + timedelta(days=i), 0),
                "label": (start + timedelta(days=i)).strftime("%b %d"),
            }
            for i in range(7)
        ]
        this_week = sum(point["thisWeek"] for point in points)
        last_week = sum(point["lastWeek"] for point in points)
        return {
            "points": points,
            "this_week": this_week,
            "last_week": last_week,
            "change": percent_change(this_week, last_week),
            "range_label": f'{points[0]["label"]} - {points[-1]["label"]}',
        }

    def get(self, request):
        now = timezone.now()
        today = now.date()
        month_start = now - timedelta(days=30)
        previous_month_start = now - timedelta(days=60)
        week_start = now - timedelta(days=7)

        def in_month(queryset, field='created_at'):
            return queryset.filter(**{f'{field}__gte': month_start})

        def in_previous_month(queryset, field='created_at'):
            return queryset.filter(**{f'{field}__gte': previous_month_start, f'{field}__lt': month_start})

        def revenue(queryset):
            return float(queryset.aggregate(total=Sum('total_amount'))['total'] or 0.0)

        def recommendations(routines):
            return sum(len(get_routine_steps(r)) for r in routines)

        sales = Order.objects.filter(status__in=REVENUE_STATUSES)
        customers = User.objects.filter(role='user')
        routines = GeneratedRoutine.objects.all()

        # 1-3. Headline totals
        total_revenue = revenue(sales)
        total_orders = Order.objects.count()
        total_customers = customers.count()

        # 4. Product Views (Using total AI recommendations as proxy for engagement)
        total_views = recommendations(routines)

        # 5. Conversion Rate (customers with a paid order / all customers * 100)
        buyers = customers.filter(orders__status__in=REVENUE_STATUSES).distinct().count()
        conversion_rate = (buyers / total_customers) * 100 if total_customers else 0.0

        # 6. Performance (last 7 days, by status)
        recent = Order.objects.filter(created_at__gte=week_start)
        new_orders = recent.filter(status__in=['pending', 'paid']).count()
        shipped_orders = recent.filter(status='shipped').count()
        delivered_orders = recent.filter(status='delivered').count()
        cancelled_orders = recent.filter(status='cancelled').count()

        # 7. Top products
        top_products = []
        for product in Product.objects.filter(order_count__gt=0).prefetch_related('images').order_by('-order_count')[:4]:
            first_image = product.images.first()
            top_products.append({
                "id": product.id,
                "name": product.title,
                "price": float(product.price),
                "units_sold": product.order_count,
                "image": request.build_absolute_uri(first_image.image.url) if first_image and first_image.image else None,
            })

        # 8. Latest orders
        latest_orders = Order.objects.select_related('payment_transaction').prefetch_related('items__product__images').order_by('-created_at')
        recent_transactions = [
            {
                "id": order.id,
                "name": order.full_name,
                "date": order.created_at.isoformat(),
                "amount": float(order.total_amount),
                "status": get_payment_status(order),
            }
            for order in latest_orders.exclude(status__in=NON_SALE_STATUSES)[:9]
        ]

        recent_orders = []
        for order in latest_orders.filter(created_at__gte=month_start)[:6]:
            items = list(order.items.all())
            first_item = items[0] if items else None
            first_image = first_item.product.images.first() if first_item else None
            recent_orders.append({
                "id": order.id,
                "product": first_item.product.title if first_item else "-",
                "sku": first_item.product.sku if first_item else "",
                "image": request.build_absolute_uri(first_image.image.url) if first_image and first_image.image else None,
                "extra_items": max(len(items) - 1, 0),
                "quantity": sum(item.quantity for item in items),
                "date": order.created_at.isoformat(),
                "status": order.status,
                "amount": float(order.total_amount),
            })

        # 9. Most ordered areas
        top_areas = list(
            Order.objects.exclude(status__in=NON_SALE_STATUSES).exclude(city='')
            .values('city').annotate(orders=Count('id')).order_by('-orders')[:5]
        )

        data = {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "total_customers": total_customers,
            "product_views": total_views,
            "conversion_rate": round(conversion_rate, 3),
            # Each headline figure compared to the 30 days before
            "changes": {
                "revenue": percent_change(revenue(in_month(sales)), revenue(in_previous_month(sales))),
                "orders": percent_change(in_month(Order.objects).count(), in_previous_month(Order.objects).count()),
                "customers": percent_change(in_month(customers, 'date_joined').count(), in_previous_month(customers, 'date_joined').count()),
                "views": percent_change(recommendations(in_month(routines)), recommendations(in_previous_month(routines))),
                "conversion": percent_change(in_month(sales).count(), in_previous_month(sales).count()),
            },
            "performance": {
                "new_orders": new_orders,
                "shipped_orders": shipped_orders,
                "delivered_orders": delivered_orders,
                "cancelled_orders": cancelled_orders,
                "total": new_orders + shipped_orders + delivered_orders + cancelled_orders,
            },
            "sale_chart": self._sale_chart(request, today),
            "order_chart": self._weekly_chart(Order.objects.all(), 'created_at', today),
            "customer_chart": self._weekly_chart(customers, 'date_joined', today),
            "top_products": top_products,
            "recent_transactions": recent_transactions,
            "recent_orders": recent_orders,
            "top_areas": top_areas,
        }

        return success_response(
            message="Dashboard summary fetched successfully",
            data=data,
            status_code=status.HTTP_200_OK
        )


class OrderListApiView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminRole]
    serializer_class = OrderListSerializer
    pagination_class = AdminPagination
    search_fields = ['id', 'full_name', 'user__email', 'phone', 'city']

    def get_queryset(self):
        orders = Order.objects.select_related('user', 'payment_transaction').prefetch_related('items__product__images').order_by('-created_at')
        order_status = self.request.query_params.get('status')
        if order_status:
            orders = orders.filter(status=order_status)
        return orders


class OrderDetailApiView(generics.RetrieveDestroyAPIView):
    permission_classes = [permissions.IsAdminRole]
    serializer_class = OrderListSerializer
    queryset = Order.objects.select_related('user').prefetch_related('items__product__images')

    def delete(self, request, *args, **kwargs):
        order = self.get_object()
        # Real sales stay on record; only abandoned orders can be removed
        if order.status not in NON_SALE_STATUSES:
            return Response(
                {"error": "Only cancelled or failed orders can be deleted. Cancel this order first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.delete()
        return success_response(
            message="Order deleted successfully",
            data=None,
            status_code=status.HTTP_200_OK
        )


def stock_was_taken(order):
    """COD takes stock when the order is placed; card orders only once payment succeeds."""
    if getattr(order, 'payment_transaction', None) is None:
        return True
    return order.status in REVENUE_STATUSES


def restock_order(order):
    for item in order.items.all():
        product = Product.objects.select_for_update().get(id=item.product_id)
        product.stock += item.quantity
        product.order_count = max(0, product.order_count - item.quantity)
        product.save(update_fields=['stock', 'order_count'])


class OrderMarkDeliveredAPIView(APIView):
    permission_classes = [permissions.IsAdminRole]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            raise Http404

        db_status = str(request.data.get('status') or 'delivered').lower().strip()
        if db_status not in [s[0] for s in Order.STATUS_CHOICES]:
            return Response({"error": "Invalid status provided"}, status=status.HTTP_400_BAD_REQUEST)

        context = {"request": request}
        if order.status == db_status:
            return success_response(
                message=f"Order is already {db_status}",
                data=OrderListSerializer(order, context=context).data,
                status_code=status.HTTP_200_OK
            )

        if order.status == 'cancelled':
            return Response(
                {"error": "A cancelled order can't be reopened."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            if db_status == 'cancelled' and stock_was_taken(order):
                restock_order(order)
            order.status = db_status
            order.save()

        return success_response(
            message=f"Order status updated to {db_status}",
            data=OrderListSerializer(order, context=context).data,
            status_code=status.HTTP_200_OK
        )

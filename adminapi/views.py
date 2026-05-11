from django.http import Http404
from rest_framework import generics
from account.models import User, PrivacyPolicy, TermsAndConditions
from .serializers import (
    UserListSerializer, PrivacyPolicyListSerializer, TermsAndConditionsListSerializer, 
    CustomerListSerializer, UserDetailSerializer, AnalyserListSerializer, 
    AnalyserDetailSerializer, AdminUserSerializer
)
from account import permissions
from category.models import Category
from category.serializers import Categorylistserializer
from skincare.response import success_response
from rest_framework import status
from django.db.models import Count, Sum, Q
from django.db.models.functions import ExtractMonth, ExtractDay, ExtractWeekDay
from shop.models import GeneratedRoutine
from product.models import Product
from django.utils import timezone
from datetime import timedelta, datetime
from rest_framework.views import APIView
from shop.models import Order
from .serializers import OrderListSerializer
import calendar

# Create your views here.

class UserListCreateApiView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAdminRole]
    
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
        self.perform_destroy(instance)
        return success_response(
            message="User deleted successfully",
            data=None,
            status_code=status.HTTP_200_OK
        )



class CategoryListCreateApiView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAdminRole]
    serializer_class = Categorylistserializer
    queryset = Category.objects.all().order_by('-id')

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

    def get_queryset(self):
        # Customers who have purchased minimum one time
        return User.objects.filter(role='user', orders__isnull=False).distinct().annotate(
            orders_count=Count('orders', distinct=True),
            total_spent=Sum('orders__total_amount')
        ).order_by('-id')


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
        self.perform_destroy(instance)
        return success_response(
            message="User deleted successfully",
            data=None,
            status_code=status.HTTP_200_OK
        )


class AnalyserListApiView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminRole]
    serializer_class = AnalyserListSerializer

    def get_queryset(self):
        return User.objects.filter(routines__isnull=False).distinct().order_by('-id')


class AnalyserDetailApiView(generics.RetrieveDestroyAPIView):
    permission_classes = [permissions.IsAdminRole]
    serializer_class = AnalyserDetailSerializer
    queryset = User.objects.all()
    lookup_field = 'pk'

    def get_object(self):
        return User.objects.filter(routines__isnull=False).distinct().get(pk=self.kwargs['pk'])

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(
            message="User deleted successfully",
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
                data = r.routine_data
                if not data:
                    continue
                
                # Handle cases where routine_data might be a string (SQLite/Mismatched migrations)
                if isinstance(data, str):
                    import json
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                
                if not isinstance(data, dict):
                    continue

                am_steps = data.get('am_routine', [])
                pm_steps = data.get('pm_routine', [])
                
                if not isinstance(am_steps, list): am_steps = []
                if not isinstance(pm_steps, list): pm_steps = []

                for step in am_steps + pm_steps:
                    if isinstance(step, dict):
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

    def get(self, request):
        # 1. Total Revenue (Sum of paid/shipped/delivered orders)
        revenue_data = Order.objects.filter(
            status__in=['paid', 'shipped', 'delivered']
        ).aggregate(total=Sum('total_amount'))
        total_revenue = float(revenue_data['total'] or 0.0)

        # 2. Total Orders
        total_orders = Order.objects.count()

        # 3. Total Customers
        total_customers = User.objects.filter(role='user').count()

        # 4. Product Views (Using total AI recommendations as proxy for engagement)
        total_views = 0
        routines = GeneratedRoutine.objects.all()
        for r in routines:
            if not r.routine_data:
                continue
            data = r.routine_data
            if isinstance(data, str):
                import json
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    continue
            
            am_steps = data.get('am_routine', []) if isinstance(data, dict) else []
            pm_steps = data.get('pm_routine', []) if isinstance(data, dict) else []
            total_views += len(am_steps) + len(pm_steps)

        # 5. Conversion Rate (Paid Orders / Total Users * 100)
        paid_orders = Order.objects.filter(status__in=['paid', 'shipped', 'delivered']).count()
        conversion_rate = 0.0
        if total_customers > 0:
            conversion_rate = (paid_orders / total_customers) * 100

        # 6. Performance (Total counts by status)
        new_orders_total = Order.objects.filter(status__in=['pending', 'paid']).count()
        shipped_orders_total = Order.objects.filter(status='shipped').count()
        delivered_orders_total = Order.objects.filter(status='delivered').count()
        cancelled_orders_total = Order.objects.filter(status='cancelled').count()

        # 7. Sale Chart (Monthly Revenue for current vs last year)
        current_year = timezone.now().year
        last_year = current_year - 1
        month_abbr = list(calendar.month_abbr)[1:]

        this_year_revenue = Order.objects.filter(
            status__in=['paid', 'shipped', 'delivered', 'completed'],
            created_at__year=current_year
        ).annotate(month=ExtractMonth('created_at')).values('month').annotate(total=Sum('total_amount'))
        
        last_year_revenue = Order.objects.filter(
            status__in=['paid', 'shipped', 'delivered', 'completed'],
            created_at__year=last_year
        ).annotate(month=ExtractMonth('created_at')).values('month').annotate(total=Sum('total_amount'))
        
        this_year_dict = {item['month']: float(item['total'] or 0) for item in this_year_revenue}
        last_year_dict = {item['month']: float(item['total'] or 0) for item in last_year_revenue}
        
        sale_chart = []
        for i in range(1, 13):
            sale_chart.append({
                "month": month_abbr[i-1],
                "thisMonth": round(this_year_dict.get(i, 0.0), 2),
                "lastMonth": round(last_year_dict.get(i, 0.0), 2)
            })

        # 8. Order Chart (Last 7 days vs Previous 7 days)
        today = timezone.now().date()
        this_week_start = today - timedelta(days=6)
        last_week_start = today - timedelta(days=13)
        last_week_end = today - timedelta(days=7)
        
        this_week_orders = Order.objects.filter(created_at__date__gte=this_week_start).values('created_at__date').annotate(count=Count('id'))
        last_week_orders = Order.objects.filter(created_at__date__gte=last_week_start, created_at__date__lte=last_week_end).values('created_at__date').annotate(count=Count('id'))
        
        this_week_dict = {item['created_at__date']: item['count'] for item in this_week_orders}
        last_week_dict = {item['created_at__date']: item['count'] for item in last_week_orders}
        
        order_chart = []
        for i in range(7):
            current_day = this_week_start + timedelta(days=i)
            prev_day = current_day - timedelta(days=7)
            
            order_chart.append({
                "day": i + 1,
                "thisWeek": this_week_dict.get(current_day, 0),
                "lastWeek": last_week_dict.get(prev_day, 0),
                "label": current_day.strftime("%b %d")
            })

        data = {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "total_customers": total_customers,
            "product_views": total_views,
            "conversion_rate": round(conversion_rate, 3),
            "performance": {
                "new_orders": new_orders_total,
                "shipped_orders": shipped_orders_total,
                "delivered_orders": delivered_orders_total,
                "cancelled_orders": cancelled_orders_total
            },
            "sale_chart": sale_chart,
            "order_chart": order_chart
        }

        return success_response(
            message="Dashboard summary fetched successfully",
            data=data,
            status_code=status.HTTP_200_OK
        )


class OrderListApiView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminRole]
    serializer_class = OrderListSerializer

    def get_queryset(self):
        return Order.objects.select_related('user').prefetch_related('items__product').order_by('-created_at')


class OrderMarkDeliveredAPIView(APIView):
    permission_classes = [permissions.IsAdminRole]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            raise Http404

        if order.status == 'delivered':
            return success_response(
                message="Order already delivered",
                data=OrderListSerializer(order).data,
                status_code=status.HTTP_200_OK
            )

        order.status = 'delivered'
        order.save()

        return success_response(
            message="Order marked as delivered",
            data=OrderListSerializer(order).data,
            status_code=status.HTTP_200_OK
        )
from rest_framework import generics
from account.models import User, PrivacyPolicy, TermsAndConditions
from .serializers import UserListSerializer, PrivacyPolicyListSerializer, TermsAndConditionsListSerializer, CustomerListSerializer, UserDetailSerializer, AnalyserListSerializer, AnalyserDetailSerializer
from account import permissions
from category.models import Category
from category.serializers import Categorylistserializer
from skincare.response import success_response
from rest_framework import status
from django.db.models import Count, Sum
from shop.models import GeneratedRoutine
from product.models import Product
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView

# Create your views here.

class UserListApiView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminRole]
    serializer_class = UserListSerializer

    def get_queryset(self):
        return User.objects.filter(role='user').select_related('profile').order_by('-id')

class UserDeleteApiView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAdminRole]
    queryset = User.objects.filter(role='user')
    lookup_field = 'pk'

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
    serializer_class = UserDetailSerializer
    queryset = User.objects.all().select_related('profile')
    lookup_field = 'pk'

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
                if not r.routine_data:
                    continue
                # JSON fields could be dicts or strings depending on DB
                data = r.routine_data
                if isinstance(data, str):
                    import json
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                
                am_steps = data.get('am_routine', []) if isinstance(data, dict) else []
                pm_steps = data.get('pm_routine', []) if isinstance(data, dict) else []
                
                for step in am_steps + pm_steps:
                    if isinstance(step, dict):
                        pid = step.get('product_id')
                        if pid:
                            counts[pid] = counts.get(pid, 0) + 1
            return counts

        current_counts = count_products(routines_current)
        previous_counts = count_products(routines_previous)
        all_counts = count_products(routines_all)

        products = Product.objects.select_related('category').filter(id__in=all_counts.keys())
        
        result = []
        category_performance = {}

        for p in products:
            total_recs = all_counts.get(p.id, 0)
            cur = current_counts.get(p.id, 0)
            prev = previous_counts.get(p.id, 0)

            # Category performance grouping
            cat_name = p.category.name if p.category else "Uncategorized"
            if cat_name not in category_performance:
                category_performance[cat_name] = {"current": 0, "previous": 0}
            
            category_performance[cat_name]["current"] += cur
            category_performance[cat_name]["previous"] += prev

            if prev == 0:
                trend_val = 100.0 if cur > 0 else 0.0
            else:
                trend_val = ((cur - prev) / prev) * 100

            trend_str = f"+{trend_val:.1f}%" if trend_val > 0 else f"{trend_val:.1f}%"
            if trend_val == 0:
                trend_str = "0.0%"

            result.append({
                "id": p.id,
                "product_name": p.title,
                "category": cat_name,
                "recommendations": total_recs,
                "trend": trend_str
            })

        result.sort(key=lambda x: x['recommendations'], reverse=True)

        performance_list = [
            {"category": cat, "current": counts["current"], "previous": counts["previous"]}
            for cat, counts in category_performance.items()
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
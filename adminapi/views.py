from rest_framework import generics
from account.models import User, PrivacyPolicy, TermsAndConditions
from .serializers import UserListSerializer, PrivacyPolicyListSerializer, TermsAndConditionsListSerializer, CustomerListSerializer, UserDetailSerializer, AnalyserListSerializer, AnalyserDetailSerializer
from account import permissions
from category.models import Category
from category.serializers import Categorylistserializer
from skincare.response import success_response
from rest_framework import status
from django.db.models import Count, Sum

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
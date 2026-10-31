from django.urls import path
from category.views import CategoryRetrieveUpdateDeleteApiView
from product.views import ProductCreateAndListApiView,ProductRetrieveUpdateDestroyApiView
from .views import UserListCreateApiView, UserDeleteApiView, CategoryListCreateApiView, CustomerListApiView
from . import views


urlpatterns = [
    # Members
    path("users/", UserListCreateApiView.as_view(), name="user-list"),
    path("users/<str:membership_id>/", views.UserDetailApiView.as_view(), name="user-detail"),
    path("users/<str:membership_id>/delete/", UserDeleteApiView.as_view(), name="user-delete"),

    # Customers
    path("customers/", CustomerListApiView.as_view(), name="customer-list"),
    path('customer/<str:membership_id>/', views.UserDetailApiView.as_view(), name='customer-detail'),
    path('customer/<str:membership_id>/delete/', views.UserDetailApiView.as_view(), name='customer-delete'),

    # Category
    path("category/", CategoryListCreateApiView.as_view(), name="category-create-and-list"),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDeleteApiView.as_view(), name='category-detail'),
    path('categorie/<int:pk>/', CategoryRetrieveUpdateDeleteApiView.as_view()),

    # Product
    path("product/", ProductCreateAndListApiView.as_view(), name="product-create-and-list"),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroyApiView.as_view(), name='product-detail'),

    # Privacy Policy
    path("privacy-policy/", views.PrivacyPolicyListCreateApiView.as_view(), name="privacy-policy-create-and-list"),
    path("privacy-policy/<int:pk>/", views.PrivacyPolicyListCreateApiView.as_view(), name="privacy-policy-detail"),

    # Terms and Conditions
    path("terms-and-conditions/", views.TermsAndConditionsListCreateApiView.as_view(), name="terms-and-conditions-create-and-list"),
    path("terms-and-conditions/<int:pk>/", views.TermsAndConditionsListCreateApiView.as_view(), name="terms-and-conditions-detail"),

    # Analyser
    path("analyser/", views.AnalyserListApiView.as_view(), name="analyser-list"),
    path("analyser/<int:pk>/", views.AnalyserDetailApiView.as_view(), name="analyser-detail"),
    path("analyser/<int:pk>/delete/", views.AnalyserDetailApiView.as_view(), name="analyser-delete"),

    # AI Analytics
    path("ai-analytics/products/", views.AIAnalyticsProductListView.as_view(), name="ai-analytics-products"),

    # Dashboard
    path("dashboard/summary/", views.DashboardSummaryView.as_view(), name="dashboard-summary"),
    
    # Orders
    path("orders/", views.OrderListApiView.as_view(), name="order-list"),
    path("orders/<int:pk>/", views.OrderDetailApiView.as_view(), name="order-detail"),
    path("orders/<int:pk>/mark-delivered/", views.OrderMarkDeliveredAPIView.as_view(), name="order-mark-delivered"),
]
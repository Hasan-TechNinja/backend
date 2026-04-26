from django.urls import path
from category.views import CategoryRetrieveUpdateDeleteApiView
from product.views import ProductCreateAndListApiView,ProductRetrieveUpdateDestroyApiView
from .views import UserListApiView, UserDeleteApiView, CategoryListCreateApiView

urlpatterns = [
    # Members
    path("users/", UserListApiView.as_view(), name="user-list"),
    path("users/<int:pk>/delete/", UserDeleteApiView.as_view(), name="user-delete"),

    # Category
    path("category/", CategoryListCreateApiView.as_view(), name="category-create-and-list"),
    path('categorie/<int:pk>/', CategoryRetrieveUpdateDeleteApiView.as_view(), name='category-detail'),

    # Product
    path("product/", ProductCreateAndListApiView.as_view(), name="product-create-and-list"),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroyApiView.as_view(), name='product-detail'),
]
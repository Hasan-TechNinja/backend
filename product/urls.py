from django.urls import path
from . import views


urlpatterns = [
    path("products/", views.ProductCreateAndListApiView.as_view(), name="products"),
    path("products/<int:pk>/", views.ProductRetrieveUpdateDestroyApiView.as_view(), name="product"),
    path("products/user/", views.ProductListApiView.as_view(), name="products"),
    path("products/user/<int:pk>/", views.ProductRetrieveApiView.as_view(), name="product"),
    path("products/best/", views.BestProductApiView.as_view(), name="best-products"),
]
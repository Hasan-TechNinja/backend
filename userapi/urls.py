from django.urls import path
from category.views import CategoryListApiview,CategoryDetailApiview
from product.views import ProductListApiView,ProductRetrieveApiView

urlpatterns = [
    
    #Category
    path('categories/', CategoryListApiview.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailApiview.as_view(), name='category-detail'),


    #Product
    path('products/', ProductListApiView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductRetrieveApiView.as_view(), name='product-detail'),

]

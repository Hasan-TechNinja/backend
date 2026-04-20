from django.urls import path
from category.views import CategoryCreateandListApiView,CategoryRetrieveUpdateDeleteApiView
from product.views import ProductCreateAndListApiView,ProductRetrieveUpdateDestroyApiView

urlpatterns = [
    #Category
    path("category/",CategoryCreateandListApiView.as_view(),name="category-create-and-list"),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDeleteApiView.as_view(), name='category-detail'),


    #Product
    path("product/",ProductCreateAndListApiView.as_view(),name="product-create-and-list"),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroyApiView.as_view(), name='product-detail'),



    
]
from django.shortcuts import render
from rest_framework.views import APIView
from skincare.response import success_response
from .models import Product,ProductImage
from .serializers import ProductCreateAndUpdateserializer, ProductListserializer
from rest_framework import status
from rest_framework.parsers import MultiPartParser,FormParser
from account.permissions import IsAdminRole,IsUserRole


# swagger 
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.

class ProductCreateAndListApiView(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser,FormParser]

    @swagger_auto_schema(
        operation_summary="get all products",
        operation_description="Endpoint to get all products. Only accessible by admin users.",
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language (EN / AR)",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        responses={
            200: openapi.Response(
                description="Product list fetched successfully",
                schema=ProductListserializer(many=True)
            ),
        },
        tags=['Product']
    )
    def get(self , request ,*args, **kwargs):
        products = Product.objects.all().order_by("created_at")
        serializer = ProductListserializer(products,many = True,context={"request": request})
        return success_response(
            message="Product list fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    
    @swagger_auto_schema(
        operation_summary="Create a new product",
        operation_description="Endpoint to create a new product. Only accessible by admin users.",
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language (EN / AR)",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        responses={
            201: openapi.Response(
                description="Product created successfully",
                schema=ProductListserializer()
            ),
            400: openapi.Response(description="Bad Request")
        },
        tags=['Product'],
    )
    def post(self , request ,*args, **kwargs):

        print(request.data)
        serializer = ProductCreateAndUpdateserializer(data=request.data,context={"request": request})
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return success_response(
            message="Product created successfully",
            data=ProductListserializer(product, context={"request": request}).data,
            status_code=status.HTTP_201_CREATED
        )




class ProductRetrieveUpdateDestroyApiView(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser,FormParser]

    @swagger_auto_schema(
        operation_summary="get a product",
        operation_description="Endpoint to get a product. Only accessible by admin users.",
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language (EN / AR)",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        responses={
            200: openapi.Response(
                description="Product fetched successfully",
                schema=ProductListserializer()
            ),
            404: openapi.Response(description="Product not found")
        },
        tags=['Product']
    )
    def get(self , request , pk , *args, **kwargs):
        product = Product.objects.get(pk=pk)
        serializer = ProductListserializer(product, context={"request": request})
        return success_response(
            message="Product fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    
    @swagger_auto_schema(
        operation_summary="Update a product",
        operation_description="Endpoint to update a product. Only accessible by admin users.",
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language (EN / AR)",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        responses={
            200: openapi.Response(
                description="Product updated successfully",
                schema=ProductListserializer()
            ),
            400: openapi.Response(description="Bad Request"),
            404: openapi.Response(description="Product not found")
        },
        tags=['Product']
    )
    def patch(self , request , pk , *args, **kwargs):
        product = Product.objects.get(pk=pk)
        serializer = ProductCreateAndUpdateserializer(product,data=request.data,partial=True,context={"request": request})
        serializer.is_valid(raise_exception=True)
        updated_product = serializer.save()
        return success_response(
            message="Product updated successfully",
            data=ProductListserializer(updated_product, context={"request": request}).data,
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Delete a product",
        operation_description="Endpoint to delete a product. Only accessible by admin users.",
        responses={
            204: openapi.Response(description="Product deleted successfully"),
            404: openapi.Response(description="Product not found")
        },
        tags=['Product']
    )
    def delete(self , request , pk , *args, **kwargs):
        product = Product.objects.get(pk=pk)
        product.delete()
        return success_response(
            message="Product deleted successfully",
            data=None,
            status_code=status.HTTP_204_NO_CONTENT
        )




class ProductListApiView(APIView):
    permission_classes = [IsUserRole]

    @swagger_auto_schema(
        operation_summary="get all products",
        operation_description="Endpoint to get all products. Only accessible by regular users.",
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language (EN / AR)",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        responses={
            200: openapi.Response(
                description="Product list fetched successfully",
                schema=ProductListserializer(many=True)
            ),
        },
        tags=['Product']
    )
    def get(self , request ,*args, **kwargs):
        products = Product.objects.all().order_by("created_at")
        serializer = ProductListserializer(products,many = True,context={"request": request})
        return success_response(
            message="Product list fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    



class ProductRetrieveApiView(APIView):
    permission_classes = [IsUserRole]

    @swagger_auto_schema(
        operation_summary="get a product",
        operation_description="Endpoint to get a product. Only accessible by regular users.",
        manual_parameters=[
            openapi.Parameter(
                'lean',
                openapi.IN_QUERY,
                description="Language (EN / AR)",
                type=openapi.TYPE_STRING,
                default='EN'
            ),
        ],
        responses={
            200: openapi.Response(
                description="Product fetched successfully",
                schema=ProductListserializer()
            ),
            404: openapi.Response(description="Product not found")
        },
        tags=['Product']
    )
    def get(self , request , pk , *args, **kwargs):
        product = Product.objects.get(pk=pk)
        serializer = ProductListserializer(product, context={"request": request})
        return success_response(
            message="Product fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )






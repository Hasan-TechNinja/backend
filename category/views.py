from django.shortcuts import render
from rest_framework.views import APIView
from skincare.response import success_response
from .models import Category
from .serializers import CategoryCreateandUpdateserializer,Categorylistserializer
from rest_framework import status
from rest_framework.parsers import MultiPartParser,FormParser
from account.permissions import IsAdminRole,IsUserRole


# swagger 
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.


class CategoryCreateandListApiView(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser,FormParser]

    @swagger_auto_schema(
        operation_summary="get all categories",
        operation_description="Endpoint to get all categories. Only accessible by admin users.",
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
                description="Category list fetched successfully",
                schema=Categorylistserializer(many=True)
            ),
        },
        tags=['Category']
    )
    def get(self , request ,*args, **kwargs):
        categories = Category.objects.all().order_by("created_at")
        serializer = Categorylistserializer(categories,many = True,context={"request": request})
        return success_response(
            message="Category list fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Create a new category",
        operation_description="Endpoint to create a new category. Only accessible by admin users.",
        request_body=CategoryCreateandUpdateserializer,
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
                description="Category created successfully",
                schema=Categorylistserializer()
            ),
            400: "Bad Request"
        },
        tags=['Category']
    )
    def post(self , request , *args, **kwargs):
        serializer = CategoryCreateandUpdateserializer(data = request.data,context={"request": request})
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return success_response(
            message="Category created successfully",
            data=Categorylistserializer(category, context={"request": request}).data,
            status_code=status.HTTP_201_CREATED
        )




class CategoryRetrieveUpdateDeleteApiView(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser,FormParser]

    @swagger_auto_schema(
        operation_summary="Retrieve a category",
        operation_description="Endpoint to get a single category by ID. Only accessible by admin users.",
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
                description="Category fetched successfully",
                schema=Categorylistserializer()
            ),
            404: "Not Found"
        },
        tags=['Category']
    )
    def get(self , request , pk ,*args , **kwargs):
        category = Category.objects.get(pk=pk)
        serializer = Categorylistserializer(category,context={"request": request})
        return success_response(
            message="Category fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    
    @swagger_auto_schema(
        operation_summary='Update a category',
        operation_description='Endpoint to update an existing category by ID. Only accessible by admin users.',
        request_body=CategoryCreateandUpdateserializer,
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
                description="Category updated successfully",
                schema=Categorylistserializer()
            ),
            400: "Bad Request",
            404: "Not Found"
        },
        tags=['Category']
    )
    def patch(self, request, pk, *args, **kwargs):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return success_response(
                message="Category not found",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = CategoryCreateandUpdateserializer(
            category, data=request.data, context={"request": request}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        category = serializer.save()

        return success_response(
            message="Category updated successfully",
            data=Categorylistserializer(category, context={"request": request}).data,
            status_code=status.HTTP_200_OK
        )


    @swagger_auto_schema(
        operation_summary="Delete a category",
        operation_description="Endpoint to delete a category by ID. Only accessible by admin users.",
        responses={
            204: "Category deleted successfully",
            404: "Not Found"
        },
        tags=['Category']
    )
    def delete(self, request, pk, *args, **kwargs):  
        category = Category.objects.get(pk=pk)
        category.delete()
        return success_response(
            message="Category deleted successfully",
            data=None,
            status_code=status.HTTP_204_NO_CONTENT
        )




class CategoryListApiview(APIView):
    permission_classes = [IsUserRole]

    @swagger_auto_schema(
        operation_summary="Get all categories",
        operation_description="Endpoint to get a list of all categories. Accessible by regular users.",
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
                description="List of categories fetched successfully",
                schema=Categorylistserializer(many=True)
            ),
        },
        tags=['Category']
    )
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all().order_by("created_at")
        serializer = Categorylistserializer(categories, many=True, context={"request": request})
        return success_response(
            message="List of categories fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )



    
class CategoryDetailApiview(APIView):
    permission_classes = [IsUserRole]

    @swagger_auto_schema(
        operation_summary="Get category details",
        operation_description="Endpoint to get details of a single category by ID. Accessible by regular users.",
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
                description="Category details fetched successfully",
                schema=Categorylistserializer()
            ),
            404: "Not Found"
        },
        tags=['Category']
    )
    def get(self, request, pk, *args, **kwargs):  
        category = Category.objects.get(pk=pk)
        serializer = Categorylistserializer(category, context={"request": request})
        return success_response(
            message="Category details fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

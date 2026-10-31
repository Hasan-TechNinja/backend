from rest_framework.permissions import AllowAny
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView
from skincare.response import success_response
from .models import Product, ProductImage
from skincare.pagination import AdminPagination
from shop.models import OrderItem
from .serializers import ProductCreateAndUpdateserializer, ProductListserializer, ProductDetailsSerializer
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from account.permissions import IsAdminRole, IsUserRole

# swagger 
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.

class ProductCreateAndListApiView(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="get all products",
        operation_description="Endpoint to get all products. Only accessible by admin users.",
        responses={
            200: openapi.Response(
                description="Product list fetched successfully",
                schema=ProductListserializer(many=True)
            ),
        },
        tags=['Product']
    )
    def get(self, request, *args, **kwargs):
        products = Product.objects.select_related("category").prefetch_related("images").order_by("-created_at")

        search = request.query_params.get("search", "").strip()
        if search:
            products = products.filter(
                Q(title__icontains=search) | Q(sku__icontains=search) | Q(category__name__icontains=search)
            )

        category = request.query_params.get("category")
        if category:
            products = products.filter(category_id=category)

        stock = request.query_params.get("stock")
        if stock == "in-stock":
            products = products.filter(stock__gt=0)
        elif stock == "out-of-stock":
            products = products.filter(stock=0)

        paginator = AdminPagination()
        page = paginator.paginate_queryset(products, request, view=self)
        serializer = ProductListserializer(page, many=True, context={"request": request})
        return success_response(
            message="Product list fetched successfully",
            data={
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            },
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Create a new product",
        operation_description="Endpoint to create a new product. Only accessible by admin users.",
        responses={
            201: openapi.Response(
                description="Product created successfully",
                schema=ProductListserializer()
            ),
            400: openapi.Response(description="Bad Request")
        },
        tags=['Product'],
    )
    def post(self, request, *args, **kwargs):
        serializer = ProductCreateAndUpdateserializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return success_response(
            message="Product created successfully",
            data=ProductListserializer(product, context={"request": request}).data,
            status_code=status.HTTP_201_CREATED
        )


class ProductRetrieveUpdateDestroyApiView(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="get a product",
        operation_description="Endpoint to get a product. Only accessible by admin users.",
        responses={
            200: openapi.Response(
                description="Product fetched successfully",
                schema=ProductListserializer()
            ),
            404: openapi.Response(description="Product not found")
        },
        tags=['Product']
    )
    def get(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductListserializer(product, context={"request": request})
        return success_response(
            message="Product fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    
    @swagger_auto_schema(
        operation_summary="Update a product",
        operation_description="Endpoint to update a product. Only accessible by admin users.",
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
    def patch(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductCreateAndUpdateserializer(product, data=request.data, partial=True, context={"request": request})
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

    def delete(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)
        # Order lines cascade with the product, so deleting it would rewrite past orders
        if OrderItem.objects.filter(product=product).exists():
            return Response(
                {"error": "This product has orders and can't be deleted. Set its stock to 0 to stop selling it."},
                status=status.HTTP_400_BAD_REQUEST
            )
        product.delete()
        return success_response(
            message="Product deleted successfully",
            data=None,
            status_code=status.HTTP_200_OK
        )


class ProductListApiView(APIView):
    permission_classes = [IsUserRole]

    @swagger_auto_schema(
        operation_summary="get all products",
        operation_description="Endpoint to get all products. Only accessible by regular users.",
        responses={
            200: openapi.Response(
                description="Product list fetched successfully",
                schema=ProductListserializer(many=True)
            ),
        },
        tags=['Product']
    )
    def get(self, request, *args, **kwargs):
        products = Product.objects.all().order_by("created_at")
        serializer = ProductListserializer(products, many=True, context={"request": request})
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
        responses={
            200: openapi.Response(
                description="Product fetched successfully",
                schema=ProductListserializer()
            ),
            404: openapi.Response(description="Product not found")
        },
        tags=['Product']
    )
    def get(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductListserializer(product, context={"request": request})
        return success_response(
            message="Product fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class BestProductApiView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="get best products",
        operation_description="Endpoint to get best products based on order_count sorted from max to min.",
        responses={
            200: openapi.Response(
                description="Best products list fetched successfully",
                schema=ProductListserializer(many=True)
            ),
        },
        tags=['Product']
    )
    def get(self, request, *args, **kwargs):
        products = Product.objects.all().order_by("-order_count")
        serializer = ProductListserializer(products, many=True, context={"request": request})
        return success_response(
            message="Best products list fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class ProductView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="get all products",
        operation_description="Endpoint to get all products with pagination, searching, and filtering.",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by title, subtitle, description, ingredients, benefits", type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('skin_type', openapi.IN_QUERY, description="Filter by skin type (oily, dry, normal, combination, sensitive)", type=openapi.TYPE_STRING),
            openapi.Parameter('min_price', openapi.IN_QUERY, description="Filter by minimum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_price', openapi.IN_QUERY, description="Filter by maximum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Sort: best, new, price_asc, price_desc", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Number of items per page", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(
                description="Product list fetched successfully",
                schema=ProductListserializer(many=True)
            ),
        },
        tags=['Product']
    )
    def get(self, request, *args, **kwargs):
        queryset = Product.objects.all().order_by("created_at")
        
        # Searching
        search_query = request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(sub_title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(key_ingredients__icontains=search_query) |
                Q(key_benefits__icontains=search_query)
            )
            
        # Filtering
        category_id = request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        skin_type = request.query_params.get('skin_type', None)
        if skin_type:
            queryset = queryset.filter(skin_type=skin_type)
            
        min_price = request.query_params.get('min_price', None)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
            
        max_price = request.query_params.get('max_price', None)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Sorting
        ordering = {
            'best': ('-order_count', '-created_at'),
            'new': ('-created_at',),
            'price_asc': ('price',),
            'price_desc': ('-price',),
        }.get(request.query_params.get('ordering', ''))
        if ordering:
            queryset = queryset.order_by(*ordering)
            
        # Pagination
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        
        # Set page size from settings or query param
        from django.conf import settings
        default_page_size = getattr(settings, 'REST_FRAMEWORK', {}).get('PAGE_SIZE', 10)
        paginator.page_size = default_page_size
        
        page_size = request.query_params.get('page_size', None)
        if page_size:
            try:
                paginator.page_size = int(page_size)
            except ValueError:
                pass
                
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = ProductListserializer(page, many=True, context={"request": request})
            paginated_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data
            }
            return success_response(
                message="Product list fetched successfully",
                data=paginated_data,
                status_code=status.HTTP_200_OK
            )
            
        serializer = ProductListserializer(queryset, many=True, context={"request": request})
        return success_response(
            message="Product list fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class ProductsDetailsView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="get a product details",
        operation_description="Endpoint to get a product details with related products. Accessible by all users.",
        responses={
            200: openapi.Response(
                description="Product details fetched successfully",
                schema=ProductDetailsSerializer()
            ),
            404: openapi.Response(description="Product not found")
        },
        tags=['Product']
    )

    def get(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductDetailsSerializer(product, context={"request": request})
        return success_response(
            message="Product fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
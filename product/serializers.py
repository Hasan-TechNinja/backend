from rest_framework import serializers
from .models import Product, ProductImage
from notifications.tasks import create_notification_task
from category.models import Category


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]


class ProductCreateAndUpdateserializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(), required=False)

    class Meta:
        model = Product
        fields = [
            "category", "title", "sub_title", "skin_type", "description",
            "key_ingredients", "how_to_use", "key_benefits", "size", "price",
            "discount", "stock", "images"
        ]

    def validate(self, attrs):
        title = attrs.get('title')
        sub_title = attrs.get('sub_title')
        skin_type = attrs.get('skin_type')
        description = attrs.get('description')
        key_ingredients = attrs.get('key_ingredients')
        how_to_use = attrs.get('how_to_use')
        key_benefits = attrs.get('key_benefits')
        size = attrs.get('size')
        price = attrs.get('price')
        discount = attrs.get('discount')
        stock = attrs.get('stock')

        if title and len(title) < 5:
            raise serializers.ValidationError({"title": "Title must be at least 5 characters long"})
        
        if sub_title and len(sub_title) < 5:
            raise serializers.ValidationError({"sub_title": "Sub title must be at least 5 characters long"})
        
        if skin_type and len(skin_type) < 3:
            raise serializers.ValidationError({"skin_type": "Skin type must be at least 3 characters long"})

        if description and len(description) < 20:
            raise serializers.ValidationError({"description": "Description must be at least 20 characters long"})
        
        if key_ingredients and len(key_ingredients) < 10:
            raise serializers.ValidationError({"key_ingredients": "Key ingredients must be at least 10 characters long"})
        
        if how_to_use and len(how_to_use) < 10:
            raise serializers.ValidationError({"how_to_use": "How to use must be at least 10 characters long"})

        if key_benefits and len(key_benefits) < 10:
            raise serializers.ValidationError({"key_benefits": "Key benefits must be at least 10 characters long"})

        if size and len(size) < 2:
            raise serializers.ValidationError({"size": "Size must be at least 2 characters long"})

        if price is not None and price < 0:
            raise serializers.ValidationError({"price": "Price must be a positive number"})

        if discount is not None and (discount < 0 or discount > 100):
            raise serializers.ValidationError({"discount": "Discount must be between 0 and 100"})

        if stock is not None and stock < 0:
            raise serializers.ValidationError({"stock": "Stock must be a positive integer"})

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        images = validated_data.pop('images', [])

        product = Product.objects.create(**validated_data)
        
        for image in images:
            ProductImage.objects.create(product=product, image=image)

        create_notification_task.delay(
            user_id=request.user.id if request and request.user else None,
            title="New Product Created",
            body=f"A new product has been created",
            data={
                "id": product.id,
                "title": product.title,
                "image": product.images.first().image.url if product.images.exists() else None   
            },
            broadcast_user=False,
            broadcast_admin=False,
            broadcast_all=True
        )

        return product

    def update(self, instance, validated_data):
        images = validated_data.pop('images', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()

        if images is not None:
            instance.images.all().delete() 
            for image in images:
                ProductImage.objects.create(product=instance, image=image)

        return instance


class ProductListserializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "category", "category_name", "title", "sub_title", "skin_type",
            "description", "key_ingredients", "how_to_use", "key_benefits", "size",
            "price", "discount", "stock", "images", "order_count", "created_at",
            "updated_at"
        ]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else ""


class ProductDetailsSerializer(ProductListserializer):
    related_products = serializers.SerializerMethodField()

    class Meta(ProductListserializer.Meta):
        fields = ProductListserializer.Meta.fields + ["related_products"]

    def get_related_products(self, obj):
        # Fetch up to 10 related products from the same category, excluding the current product
        related = Product.objects.filter(category=obj.category).exclude(id=obj.id).order_by("-order_count")[:10]
        return ProductListserializer(related, many=True, context=self.context).data


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "image", "created_at", "updated_at"]

    def validate(self, attrs):
        name = attrs.get('name')
        image = attrs.get('image')

        if name and len(name) < 3:
            raise serializers.ValidationError({"name": "Name must be at least 3 characters long"})
        
        if image and image.size > 5 * 1024 * 1024:
            raise serializers.ValidationError({"image": "Image must be less than 5MB"})
        
        return attrs
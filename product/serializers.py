from rest_framework import serializers
from .models import Product, ProductImage, StorefrontSettings
from notifications.tasks import create_notification_task
import json
import logging

logger = logging.getLogger(__name__)
from category.models import Category


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]


# Icons the storefront can draw next to a benefit
BENEFIT_ICONS = [
    "droplet", "shield", "heart-handshake", "sparkles", "feather", "shield-check",
    "leaf", "sun", "moon", "flask", "gem", "flower",
]

PAGE_TEXT_FIELDS = [
    "hero_eyebrow", "image_badge", "why_heading", "why_body", "ingredients_heading",
    "ingredients_body", "ingredients_badge", "texture_heading", "texture_body", "ritual_heading",
]
# Keys of each list item; None means a plain list of strings
PAGE_LIST_FIELDS = {
    "benefits": ("icon", "label"),
    "concerns": None,
    "ingredients": ("name", "description"),
    "texture_points": ("title", "description"),
    "morning_ritual": ("title", "description"),
    "night_ritual": ("title", "description"),
    "specifications": ("label", "value"),
    "suitable_for": None,
    "faqs": ("question", "answer"),
}
PAGE_IMAGE_FIELDS = ["ingredients_image", "texture_image"]
TRANSLATABLE_FIELDS = ["title", "sub_title", "size", *PAGE_TEXT_FIELDS, *PAGE_LIST_FIELDS]
TRANSLATION_LANGUAGES = ["ar"]
MAX_LIST_ITEMS = 30
MAX_ITEM_TEXT = 2000


def clean_page_list(field, value):
    """Trim a section list, drop blank rows and reject anything that isn't the expected shape."""
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise serializers.ValidationError({field: "Must be a list."})
    if len(value) > MAX_LIST_ITEMS:
        raise serializers.ValidationError({field: f"Use at most {MAX_LIST_ITEMS} items."})

    keys = PAGE_LIST_FIELDS[field]
    cleaned = []
    for item in value:
        if keys is None:
            if not isinstance(item, str):
                raise serializers.ValidationError({field: "Each item must be text."})
            if item.strip():
                cleaned.append(item.strip()[:MAX_ITEM_TEXT])
            continue

        if not isinstance(item, dict):
            raise serializers.ValidationError({field: f"Each item needs {', '.join(keys)}."})
        row = {key: str(item.get(key) or "").strip()[:MAX_ITEM_TEXT] for key in keys}
        if "icon" in row and row["icon"] not in BENEFIT_ICONS:
            row["icon"] = "sparkles"
        if any(row[key] for key in keys if key != "icon"):
            cleaned.append(row)
    return cleaned


def clean_translations(value):
    if value in (None, ""):
        return {}
    if not isinstance(value, dict):
        raise serializers.ValidationError({"translations": "Must be an object keyed by language."})

    cleaned = {}
    for language, fields in value.items():
        if language not in TRANSLATION_LANGUAGES:
            raise serializers.ValidationError({"translations": f"Unsupported language: {language}"})
        if not isinstance(fields, dict):
            raise serializers.ValidationError({"translations": f"{language} must be an object."})

        cleaned_fields = {}
        for field, text in fields.items():
            if field not in TRANSLATABLE_FIELDS:
                raise serializers.ValidationError({"translations": f"{field} can't be translated."})
            if field in PAGE_LIST_FIELDS:
                items = clean_page_list(field, text)
                if items:
                    cleaned_fields[field] = items
            elif isinstance(text, str) and text.strip():
                cleaned_fields[field] = text.strip()[:MAX_ITEM_TEXT]
        if cleaned_fields:
            cleaned[language] = cleaned_fields
    return cleaned


class JSONTextField(serializers.JSONField):
    """Accepts real JSON or a JSON string, since the product form is sent as multipart."""

    def to_internal_value(self, data):
        if isinstance(data, (str, bytes)):
            try:
                data = json.loads(data) if data else None
            except ValueError:
                raise serializers.ValidationError("Invalid JSON.")
        return super().to_internal_value(data)


class ProductCreateAndUpdateserializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(), required=False)
    benefits = JSONTextField(required=False)
    concerns = JSONTextField(required=False)
    ingredients = JSONTextField(required=False)
    texture_points = JSONTextField(required=False)
    morning_ritual = JSONTextField(required=False)
    night_ritual = JSONTextField(required=False)
    specifications = JSONTextField(required=False)
    suitable_for = JSONTextField(required=False)
    faqs = JSONTextField(required=False)
    translations = JSONTextField(required=False)
    clear_ingredients_image = serializers.BooleanField(required=False, write_only=True)
    clear_texture_image = serializers.BooleanField(required=False, write_only=True)

    class Meta:
        model = Product
        fields = [
            "category", "title", "sub_title", "skin_type", "description",
            "key_ingredients", "how_to_use", "key_benefits", "size", "sku", "price",
            "discount", "stock", "images",
            *PAGE_TEXT_FIELDS, *PAGE_LIST_FIELDS, *PAGE_IMAGE_FIELDS, "translations",
            "clear_ingredients_image", "clear_texture_image",
        ]

    def validate_sku(self, value):
        # Blank means no SKU; two blanks must not collide on the unique index
        return (value or '').strip() or None

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

        for field in PAGE_LIST_FIELDS:
            if field in attrs:
                attrs[field] = clean_page_list(field, attrs[field])
        if "translations" in attrs:
            attrs["translations"] = clean_translations(attrs["translations"])

        for field in PAGE_IMAGE_FIELDS:
            image = attrs.get(field)
            if image and image.size > 5 * 1024 * 1024:
                raise serializers.ValidationError({field: "Image must be less than 5MB"})

        return attrs

    def pop_cleared_images(self, validated_data):
        return [
            field for field in PAGE_IMAGE_FIELDS
            if validated_data.pop(f"clear_{field}", False) and not validated_data.get(field)
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        images = validated_data.pop('images', [])
        self.pop_cleared_images(validated_data)

        product = Product.objects.create(**validated_data)
        
        for image in images:
            ProductImage.objects.create(product=product, image=image)

        # A message broker outage must not fail the save
        try:
            create_notification_task.apply_async(kwargs=dict(
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
            ), retry=False, ignore_result=True)
        except Exception as e:
            logger.error(f"Could not queue product notification: {e}")

        return product

    def update(self, instance, validated_data):
        images = validated_data.pop('images', None)

        for field in self.pop_cleared_images(validated_data):
            setattr(instance, field, None)

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
            "description", "key_ingredients", "how_to_use", "key_benefits", "size", "sku",
            "price", "discount", "stock", "images", "order_count", "created_at",
            "updated_at"
        ]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else ""


class ProductPageSerializer(ProductListserializer):
    """A product with everything its page shows."""

    class Meta(ProductListserializer.Meta):
        fields = ProductListserializer.Meta.fields + [
            *PAGE_TEXT_FIELDS, *PAGE_LIST_FIELDS, *PAGE_IMAGE_FIELDS, "translations",
        ]


class ProductDetailsSerializer(ProductPageSerializer):
    related_products = serializers.SerializerMethodField()

    class Meta(ProductPageSerializer.Meta):
        fields = ProductPageSerializer.Meta.fields + ["related_products"]

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

class StorefrontSettingsSerializer(serializers.ModelSerializer):
    featured_product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), allow_null=True, required=False
    )
    featured_product_title = serializers.SerializerMethodField()
    shows_single_product = serializers.BooleanField(read_only=True)

    class Meta:
        model = StorefrontSettings
        fields = [
            "single_product_mode", "featured_product", "featured_product_title",
            "shows_single_product", "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def get_featured_product_title(self, obj):
        return obj.featured_product.title if obj.featured_product else None

    def validate(self, attrs):
        single = attrs.get("single_product_mode", self.instance.single_product_mode)
        featured = attrs.get("featured_product", self.instance.featured_product)
        if single and featured is None:
            raise serializers.ValidationError({"featured_product": "Choose the product to show."})
        return attrs


def public_storefront_data(settings_row):
    """What the shop needs to build its nav and decide where /products leads."""
    product = settings_row.featured_product if settings_row.shows_single_product else None
    if product is None:
        return {"single_product_mode": False, "featured_product": None}
    return {
        "single_product_mode": True,
        "featured_product": {
            "id": product.id,
            "title": product.title,
            "title_ar": (product.translations or {}).get("ar", {}).get("title") or None,
        },
    }

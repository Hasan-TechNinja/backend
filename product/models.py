from django.db import models
from category.models import Category
import random
import string

# Create your models here.

SKIN_TYPE_CHOICES = [
    ('oily', 'Oily'),
    ('dry', 'Dry'),
    ('normal', 'Normal'),
    ('combination', 'Combination'),
    ('sensitive', 'Sensitive'),
]

class Product(models.Model):
    title = models.CharField(max_length=255)
    sub_title = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    size = models.CharField(max_length=100, blank=True, null=True)
    discount = models.DecimalField(max_digits=5,decimal_places=2,default=0.00,help_text="Discount percentage or amount")
    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name='products')
    stock = models.PositiveIntegerField(default=0)
    # reserved_stock = models.PositiveIntegerField(default=0)
    # is_available = models.BooleanField(default=True)
    key_ingredients = models.TextField(blank=True, null=True)
    skin_type = models.CharField(max_length=100, blank=True, null=True, choices=SKIN_TYPE_CHOICES)
    key_benefits = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    how_to_use = models.TextField(blank=True, null=True)
    # video = models.FileField(upload_to='products/videos/', blank=True, null=True)
    order_count = models.PositiveIntegerField(default=0)

    # Product page sections. List items are stored as JSON, see PAGE_LIST_FIELDS in serializers.
    hero_eyebrow = models.CharField(max_length=120, blank=True, default='')
    image_badge = models.CharField(max_length=120, blank=True, default='')
    benefits = models.JSONField(default=list, blank=True)
    why_heading = models.CharField(max_length=255, blank=True, default='')
    why_body = models.TextField(blank=True, default='')
    concerns = models.JSONField(default=list, blank=True)
    ingredients_heading = models.CharField(max_length=255, blank=True, default='')
    ingredients_body = models.TextField(blank=True, default='')
    ingredients_badge = models.CharField(max_length=120, blank=True, default='')
    ingredients_image = models.ImageField(upload_to='products/sections/', blank=True, null=True)
    ingredients = models.JSONField(default=list, blank=True)
    texture_heading = models.CharField(max_length=255, blank=True, default='')
    texture_body = models.TextField(blank=True, default='')
    texture_image = models.ImageField(upload_to='products/sections/', blank=True, null=True)
    texture_points = models.JSONField(default=list, blank=True)
    ritual_heading = models.CharField(max_length=255, blank=True, default='')
    morning_ritual = models.JSONField(default=list, blank=True)
    night_ritual = models.JSONField(default=list, blank=True)
    specifications = models.JSONField(default=list, blank=True)
    suitable_for = models.JSONField(default=list, blank=True)
    faqs = models.JSONField(default=list, blank=True)
    # Arabic copies of the text above, e.g. {"ar": {"title": ..., "faqs": [...]}}
    translations = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_sku(self):
        prefix = (self.category.name[:2] if self.category.name and len(self.category.name) >= 2 else "PR").upper()

        random_number = ''.join(random.choices(string.digits, k=8))

        return f"{prefix}{random_number}"

    # def save(self, *args, **kwargs):
    #     if not self.sku:
    #         sku = self.generate_sku()

    #         # ensure uniqueness
    #         while Product.objects.filter(sku=sku).exists():
    #             sku = self.generate_sku()

    #         self.sku = sku

    #     super().save(*args, **kwargs)


    def __str__(self):
        return self.title
    


class ProductImage(models.Model):

    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='images')
    image = models.ImageField(upload_to='products/images/',blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Image of {self.product.title}"


class StorefrontSettings(models.Model):
    """Site-wide shop settings. There is a single row, read with load()."""

    # While on, the shop nav and /products lead straight to the featured product
    single_product_mode = models.BooleanField(default=True)
    featured_product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, blank=True, null=True, related_name='+'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Storefront settings"
        verbose_name_plural = "Storefront settings"

    @classmethod
    def load(cls):
        settings_row, _ = cls.objects.get_or_create(pk=1)
        return settings_row

    @property
    def shows_single_product(self):
        return self.single_product_mode and self.featured_product_id is not None

    def __str__(self):
        return "Storefront settings"

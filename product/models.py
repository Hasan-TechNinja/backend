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

from django.contrib import admin
from .models import Product, ProductImage
from django.utils.html import format_html

# Register your models here.

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'image_preview',)
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = "Preview"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "id", "category_name", "title", "sub_title", "skin_type",
        "short_description", "short_key_ingredients", "short_how_to_use",
        "short_key_benefits", "size", "price", "discount", "stock",
        "created_at", "updated_at"
    )
    search_fields = ("title", "category__name",)
    list_filter = ("created_at", "category")
    inlines = [ProductImageInline]

    def truncate_words(self, text, num_words=20):
        if not text:
            return ""
        words = str(text).split()
        return " ".join(words[:num_words]) + ("..." if len(words) > num_words else "")
    
    def short_description(self, obj):
        return self.truncate_words(obj.description)
    short_description.short_description = "Description"

    def short_key_ingredients(self, obj):
        return self.truncate_words(obj.key_ingredients)
    short_key_ingredients.short_description = "Key Ingredients"

    def short_how_to_use(self, obj):
        return self.truncate_words(obj.how_to_use)
    short_how_to_use.short_description = "How to Use"

    def short_key_benefits(self, obj):
        return self.truncate_words(obj.key_benefits)
    short_key_benefits.short_description = "Key Benefits"

    def category_name(self, obj):
       return obj.category.name if obj.category else ""
    category_name.short_description = "Category"

    # def video_preview(self, obj):
    #     if obj.video:
    #         return format_html(
    #             '<video width="80" height="60" controls>'
    #             '<source src="{}" type="video/mp4">'
    #             '</video>',
    #             obj.video.url
    #         )
    #     return "No Video"
    # video_preview.short_description = "Video"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "image_preview", "created_at", "updated_at")
    search_fields = ("product__title",)
    list_filter = ("created_at",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = "Image"
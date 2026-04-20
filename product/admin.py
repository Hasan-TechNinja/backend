from django.contrib import admin
from .models import Product, ProductImage
from django.utils.html import format_html

# Register your models here.

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = ("id"  , "category_name","category_name_arabic", "title","title_arabic" ,"sub_title","sub_title_arabic","skin_type","skin_type_arabic","short_description","short_description_arabic","short_key_ingredients","short_key_ingredients_arabic","short_how_to_use","short_how_to_use_arabic","short_key_benefits","short_key_benefits_arabic","sku","size", "price" , "discount" , "stock" , "reserved_stock","is_available", "video_preview","created_at" , "updated_at")
    search_fields = ("title" , "category__name","category__name_arabic","sku",)
    list_filter = ("created_at",)

    def truncate_words(self, text, num_words=20):
        if not text:
            return ""
        words = text.split()
        return " ".join(words[:num_words]) + ("..." if len(words) > num_words else "")
    
    def short_description(self, obj):
        return self.truncate_words(obj.description)
    
    short_description.short_description = "Description"

    def short_description_arabic(self, obj):
        return self.truncate_words(obj.description_arabic)
    
    short_description_arabic.short_description = "Description (Arabic)"

    def short_key_ingredients(self, obj):
        return self.truncate_words(obj.key_ingredients)

    short_key_ingredients.short_description = "Key Ingredients"

    def short_key_ingredients_arabic(self, obj):
        return self.truncate_words(obj.key_ingredients_arabic)

    short_key_ingredients_arabic.short_description = "Key Ingredients (Arabic)"


    def short_how_to_use(self, obj):
        return self.truncate_words(obj.how_to_use)
    short_how_to_use.short_description = "How to Use"

    def short_how_to_use_arabic(self, obj):
        return self.truncate_words(obj.how_to_use_arabic)
    short_how_to_use_arabic.short_description = "How to Use (Arabic)"

    def short_key_benefits(self, obj):
        return self.truncate_words(obj.key_benefits)
    short_key_benefits.short_description = "Key Benefits"

    def short_key_benefits_arabic(self, obj):
        return self.truncate_words(obj.key_benefits_arabic)

    short_key_benefits_arabic.short_description = "Key Benefits (Arabic)"

    def category_name(self, obj):
       return obj.category.name if obj.category else ""
    
    category_name.short_description = "Category"

    def category_name_arabic(self, obj):
       return obj.category.name_arabic if obj.category else ""
    
    category_name_arabic.short_description = "Category (Arabic)"


    def video_preview(self, obj):
        if obj.video:
            return format_html(
                '<video width="80" height="60" controls>'
                '<source src="{}" type="video/mp4">'
                '</video>',
                obj.video.url
            )
        return "No Video"

    video_preview.short_description = "Video"




@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("id" , "product" , "image_preview" , "created_at" , "updated_at")
    search_fields = ("product__title",)
    list_filter = ("created_at",)

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="50" height="50" style="object-fit:cover;" />'
        return "No Image"
    
    image_preview.allow_tags = True
    image_preview.short_description = "Image"
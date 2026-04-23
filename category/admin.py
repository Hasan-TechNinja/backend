from django.contrib import admin
from .models import Category
from django.utils.html import format_html

# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = ("id" , "name" , "image_preview" , "created_at" , "updated_at")
    search_fields = ("name",)
    list_filter = ("created_at",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover;" />', obj.image.url)
        return "No Image"
    
    image_preview.short_description = "Image"

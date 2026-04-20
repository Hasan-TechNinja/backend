from django.contrib import admin
from .models import Category

# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = ("id" , "name" , "name_arabic","image_preview" , "created_at" , "updated_at")
    search_fields = ("name" , "name_arabic",)
    list_filter = ("created_at",)

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="50" height="50" style="object-fit:cover;" />'
        return "No Image"
    
    image_preview.allow_tags = True
    image_preview.short_description = "Image"
    



from django.db import models

# Create your models here.


class Category(models.Model):
    
    image = models.ImageField(upload_to="categories/",blank=True, null=True)


    name = models.CharField(max_length=400,blank=True, null=True)


    name_arabic = models.CharField(max_length=400, blank=True, null=True)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

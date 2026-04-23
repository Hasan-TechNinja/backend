from rest_framework import serializers
from .models import Category
from notifications.tasks import create_notification_task


class CategoryCreateandUpdateserializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name','image']

    def validate(self, attrs):
        name = attrs.get('name')
        if name and len(name) < 2:
            raise serializers.ValidationError({"name": "name must be at least 2 characters long"})
        return attrs
    
    def create(self, validated_data):
        request = self.context.get("request")
        category = Category.objects.create(**validated_data)
        
        create_notification_task.delay(
            user_id=request.user.id if request and request.user else None,
            title="New Category Created",
            body=f"A new category has been created",
            data={
                "id": category.id,
                "name": category.name,
                "image": category.image.url if category.image else None    
            },
            broadcast_user=False,
            broadcast_admin=False,
            broadcast_all=True
        )

        return category
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    

class Categorylistserializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name','image','created_at','updated_at']

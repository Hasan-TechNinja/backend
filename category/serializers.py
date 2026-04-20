from rest_framework import serializers
from .models import Category
from skincare.translation import translate_text
from notifications.tasks import create_notification_task
from skincare.utils import TranslatedField


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
        lean = request.query_params.get('lean', 'EN').strip().upper()

        name = validated_data.get('name')
        image = validated_data.get('image')

        data={}

        if lean == "EN":
            data = {
                "name" : name,
                "image" : image,
                "name_arabic" : translate_text(name,target_language="AR")
            }
        else:
            data = {
                "name_arabic" : name,
                "image" : image,
                "name" : translate_text(name , target_language="EN")
            }

        category = Category.objects.create(**data)
        create_notification_task.delay(
            user_id=request.user.id,
            title="New Category Created",
            body=f"A new category has been created",
            data={
                "id": category.id,
                "name": category.name if lean == "EN" else category.name_arabic,
                "image": category.image.url if category.image else None    
            },
            broadcast_user=False,
            broadcast_admin=False,
            broadcast_all=True
        )

        return category
    
    def update(self, instance, validated_data):
        request = self.context.get("request")
        lean = request.query_params.get('lean', 'EN').upper() if request else "EN"

        name = validated_data.get('name', instance.name)
        image = validated_data.get('image', instance.image)

        if lean == "EN":
            instance.name = name
            instance.name_arabic = translate_text(name,target_language="AR")
        else:
            instance.name = translate_text(name , target_language="EN")
            instance.name_arabic = name

        instance.image = image
        instance.save()

        return instance
    



class Categorylistserializer(serializers.ModelSerializer):
    name = TranslatedField("name", "name_arabic")

    class Meta:
        model = Category
        fields = ['id','name','image','created_at','updated_at']




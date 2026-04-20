from rest_framework import serializers
from .models import Product , ProductImage
from skincare.translation import translate_text
from skincare.utils import TranslatedField
from notifications.tasks import create_notification_task
from category.models import Category


class ProductCreateAndUpdateserializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(), required = False)
    
    class Meta:
        model = Product
        fields = ["category","title","sub_title","skin_type","description","key_ingredients","how_to_use","key_benefits","size","price","discount","stock","is_available","video","images"]

    def validate(self, attrs):
        category = attrs.get('category')
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
        is_available = attrs.get('is_available')

        if not Category.objects.filter(id=category.id).exists():
            raise serializers.ValidationError({
                "category": "Selected category does not exist"
            })
        
        if title and len(title) < 5:
            raise serializers.ValidationError({
                "title": "Title must be at least 5 characters long"
            })
        
        if sub_title and len(sub_title) < 10:
            raise serializers.ValidationError({
                "sub_title": "Sub title must be at least 5 characters long"
            })
        
        if skin_type and len(skin_type) < 3:
            raise serializers.ValidationError({
                "skin_type": "Skin type must be at least 3 characters long"
            })
        if description and len(description) < 20:
            raise serializers.ValidationError({
                "description": "Description must be at least 20 characters long"
            })
        
        if key_ingredients and len(key_ingredients) < 10:
            raise serializers.ValidationError({
                "key_ingredients": "Key ingredients must be at least 10 characters long"
            })
        
        if how_to_use and len(how_to_use) < 10:
            raise serializers.ValidationError({
                "how_to_use": "How to use must be at least 10 characters long"
            })
        if key_benefits and len(key_benefits) < 10:
            raise serializers.ValidationError({
                "key_benefits": "Key benefits must be at least 10 characters long"
            })
        if size and len(size) < 2:
            raise serializers.ValidationError({
                "size": "Size must be at least 2 characters long"
            })
        if price is not None and price < 0:
            raise serializers.ValidationError({
                "price": "Price must be a positive number"
            })
        if discount is not None and (discount < 0 or discount > 100):
            raise serializers.ValidationError({
                "discount": "Discount must be between 0 and 100"
            })
        if stock is not None and stock < 0:
            raise serializers.ValidationError({
                "stock": "Stock must be a positive integer"
            })
        return attrs
    
    def create(self, validated_data):
        request = self.context.get("request")
        lean = request.query_params.get('lean', 'EN').strip().upper() if request else "EN"

        category = validated_data.get('category')
        title = validated_data.get('title')
        sub_title = validated_data.get('sub_title')
        skin_type = validated_data.get('skin_type')
        description = validated_data.get('description')
        key_ingredients = validated_data.get('key_ingredients')
        how_to_use = validated_data.get('how_to_use')
        key_benefits = validated_data.get('key_benefits')
        size = validated_data.get('size')
        price = validated_data.get('price')
        discount = validated_data.get('discount')
        stock = validated_data.get('stock')
        is_available = validated_data.get('is_available')
        video = validated_data.get('video')
        images = validated_data.get('images', [])

        productdata = {}
        if lean == "EN":
            productdata = {
                "category" : category,

                "title" : title,
                "sub_title" : sub_title,
                "skin_type" : skin_type,
                "description" : description,
                "key_ingredients" : key_ingredients,
                "how_to_use" : how_to_use,
                "key_benefits" : key_benefits,

                "size" : size,
                "price" : price,
                "discount" : discount,
                "stock" : stock,
                "is_available" : is_available,
                "video" : video,

                "title_arabic" : translate_text(title,target_language="AR"),
                "sub_title_arabic" : translate_text(sub_title,target_language="AR") if sub_title else "",
                "skin_type_arabic" : translate_text(skin_type,target_language="AR") if skin_type else "",
                "description_arabic" : translate_text(description,target_language="AR") if description else "",
                "key_ingredients_arabic" : translate_text(key_ingredients,target_language="AR") if key_ingredients else "",
                "how_to_use_arabic" : translate_text(how_to_use,target_language="AR") if how_to_use else "",
                "key_benefits_arabic" : translate_text(key_benefits,target_language="AR") if key_benefits else ""
            }
        else:
            productdata = {
                "category" : category,
                "title_arabic" : title,
                "sub_title_arabic" : sub_title,
                "skin_type_arabic" : skin_type,
                "description_arabic" : description,
                "key_ingredients_arabic" : key_ingredients,
                "how_to_use_arabic" : how_to_use,
                "key_benefits_arabic" : key_benefits,
                "size" : size,
                "price" : price,
                "discount" : discount,
                "stock" : stock,
                "is_available" : is_available,
                "video" : video,
                "title" : translate_text(title , target_language="EN"),
                "sub_title" : translate_text(sub_title , target_language="EN") if sub_title else "",
                "skin_type" : translate_text(skin_type , target_language="EN") if skin_type else "",
                "description" : translate_text(description , target_language="EN") if description else "",
                "key_ingredients" : translate_text(key_ingredients , target_language="EN") if key_ingredients else "",
                "how_to_use" : translate_text(how_to_use , target_language="EN") if how_to_use else "",
                "key_benefits" : translate_text(key_benefits , target_language="EN") if key_benefits else ""
            }
        product  = Product.objects.create(**productdata)
        for image in images:
            ProductImage.objects.create(product=product,image=image)


        create_notification_task.delay(
            user_id=request.user.id,
            title="New Product Created",
            body=f"A new product has been created",
            data={
                "id": product.id,
                "title": product.title if lean == "EN" else product.title_arabic,
                "image": product.images.first().image.url if product.images.exists() else None   
            },
            broadcast_user=False,
            broadcast_admin=False,
            broadcast_all=True
        )

        return product

    def update(self, instance, validated_data):
        request = self.context.get("request")
        lean = request.query_params.get('lean', 'EN').upper() if request else "EN"
        
        category = validated_data.get('category', instance.category)
        title = validated_data.get('title', instance.title)
        sub_title = validated_data.get('sub_title', instance.sub_title)
        skin_type = validated_data.get('skin_type', instance.skin_type)
        description = validated_data.get('description', instance.description)
        key_ingredients = validated_data.get('key_ingredients', instance.key_ingredients)
        how_to_use = validated_data.get('how_to_use', instance.how_to_use)
        key_benefits = validated_data.get('key_benefits', instance.key_benefits)
        size = validated_data.get('size', instance.size)
        price = validated_data.get('price', instance.price)
        discount = validated_data.get('discount', instance.discount)
        stock = validated_data.get('stock', instance.stock)
        is_available = validated_data.get('is_available', instance.is_available)
        video = validated_data.get('video', instance.video)
        images = validated_data.get('images', [])
        if lean == "EN":
            instance.category = category
            instance.title = title
            instance.sub_title = sub_title
            instance.skin_type = skin_type
            instance.description = description
            instance.key_ingredients = key_ingredients
            instance.how_to_use = how_to_use
            instance.key_benefits = key_benefits
            instance.size = size
            instance.price = price
            instance.discount = discount
            instance.stock = stock
            instance.is_available = is_available

            instance.title_arabic = translate_text(title,target_language="AR")
            instance.sub_title_arabic = translate_text(sub_title,target_language="AR") if sub_title else ""
            instance.skin_type_arabic = translate_text(skin_type,target_language="AR") if skin_type else ""
            instance.description_arabic = translate_text(description,target_language="AR") if description else ""
            instance.key_ingredients_arabic = translate_text(key_ingredients,target_language="AR") if key_ingredients else ""
            instance.how_to_use_arabic = translate_text(how_to_use,target_language="AR") if how_to_use else ""
            instance.key_benefits_arabic = translate_text(key_benefits,target_language="AR") if key_benefits else ""
        else:
            instance.category = category
            instance.title_arabic = title
            instance.sub_title_arabic = sub_title
            instance.skin_type_arabic = skin_type
            instance.description_arabic = description
            instance.key_ingredients_arabic = key_ingredients
            instance.how_to_use_arabic = how_to_use
            instance.key_benefits_arabic = key_benefits
            instance.size = size
            instance.price = price
            instance.discount = discount
            instance.stock = stock
            instance.is_available = is_available

            instance.title = translate_text(title , target_language="EN")
            instance.sub_title = translate_text(sub_title , target_language="EN") if sub_title else ""
            instance.skin_type = translate_text(skin_type , target_language="EN") if skin_type else ""
            instance.description = translate_text(description , target_language="EN") if description else ""
            instance.key_ingredients = translate_text(key_ingredients , target_language="EN") if key_ingredients else ""
            instance.how_to_use = translate_text(how_to_use , target_language="EN") if how_to_use else ""
            instance.key_benefits = translate_text(key_benefits , target_language="EN") if key_benefits else ""

        instance.video = video
        instance.save()

        if images is not None:
            instance.images.all().delete() 

            for image in images:
                ProductImage.objects.create(product=instance, image=image)

        return instance




class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]


        


class ProductListserializer(serializers.ModelSerializer):

    title = TranslatedField("title", "title_arabic")
    sub_title = TranslatedField("sub_title", "sub_title_arabic")
    skin_type = TranslatedField("skin_type", "skin_type_arabic")
    description = TranslatedField("description", "description_arabic")
    key_ingredients = TranslatedField("key_ingredients", "key_ingredients_arabic")
    how_to_use = TranslatedField("how_to_use", "how_to_use_arabic")
    key_benefits = TranslatedField("key_benefits", "key_benefits_arabic")
    category_name = serializers.SerializerMethodField()

    images = ProductImageSerializer(many=True, read_only=True)


    
    class Meta:
        model = Product
        fields = ["id","category","category_name","title","sub_title","skin_type","description","key_ingredients","how_to_use","key_benefits","size","sku","price","discount","stock","reserved_stock","is_available","video","images","created_at","updated_at"]

    def get_category_name(self, obj):
        request = self.context.get("request")
        if not request:
            return obj.category.name
        
        lean = self.context.get("request").query_params.get("lean", "EN")

        if lean == "AR":
            return obj.category.name_arabic
        return obj.category.name



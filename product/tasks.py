from celery import shared_task
from .models import Product
from deep_translator import GoogleTranslator
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def translate_product_task(self, product_id):
    try:
        product = Product.objects.get(id=product_id)
        translator = GoogleTranslator(source='en', target='ar')

        fields_to_translate = [
            'title', 'sub_title', 'description', 
            'key_ingredients', 'key_benefits', 'how_to_use'
        ]

        updated = False
        for field in fields_to_translate:
            english_text = getattr(product, field)
            arabic_field = f"{field}_arabic"
            
            if english_text and not getattr(product, arabic_field):
                try:
                    translated_text = translator.translate(english_text)
                    setattr(product, arabic_field, translated_text)
                    updated = True
                except Exception as e:
                    logger.error(f"Error translating field {field} for product {product_id}: {e}")

        if updated:
            product.save(update_fields=[f"{f}_arabic" for f in fields_to_translate])
            logger.info(f"Successfully translated product {product_id} to Arabic")

    except Product.DoesNotExist:
        logger.error(f"Product {product_id} does not exist for translation")
    except Exception as e:
        logger.error(f"Unexpected error in translate_product_task for product {product_id}: {e}")
        raise self.retry(exc=e, countdown=60)

from celery import shared_task
from .models import Order
from .services import OmnifulService
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def sync_order_to_omniful(self, order_id):
    """
    Celery task to push the full order payload to Omniful.
    Implements a retry mechanism on failure.
    """
    try:
        order = Order.objects.get(id=order_id)
        service = OmnifulService()
        
        # Prepare payload mapping
        items = []
        for item in order.items.all():
            # Fallback to ID if sku is not available
            sku = getattr(item.product, 'sku', f"PROD-{item.product.id}")
            if not sku:
                sku = f"PROD-{item.product.id}"
                
            items.append({
                'sku': sku,
                'variant_sku': sku, # Often required by OMS
                'quantity': item.quantity,
                'price': float(item.price),
                'name': item.product.title
            })
            
        payload = {
            'order_reference': str(order.id),
            'total_amount': float(order.total_amount),
            'currency': 'SAR',
            'status': order.status,
            'customer': {
                'first_name': order.first_name,
                'last_name': order.last_name,
                'email': order.email,
                'phone': order.phone
            },
            'shipping_address': {
                'address_line1': order.address_line1,
                'address_line2': order.address_line2,
                'city': order.city,
                'state': order.state,
                'postal_code': order.postal_code,
                'country': order.country
            },
            'line_items': items,
            'metadata': {
                'hyperpay_checkout_id': getattr(order.payment_transaction, 'checkout_id', ''),
                'hyperpay_transaction_id': getattr(order.payment_transaction, 'transaction_id', '')
            }
        }
        
        service.create_order(payload)
        logger.info(f"Successfully synced order {order_id} to Omniful")
        
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for Omniful sync")
    except Exception as exc:
        logger.error(f"Error syncing order {order_id} to Omniful: {exc}")
        # Retry with exponential backoff (default retry)
        raise self.retry(exc=exc, countdown=300) # 5 minutes

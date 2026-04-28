import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class HyperPayService:
    def __init__(self):
        self.base_url = getattr(settings, 'HYPERPAY_BASE_URL', 'https://test.oppwa.com')
        self.bearer_token = getattr(settings, 'HYPERPAY_BEARER_TOKEN', '')
        self.headers = {
            'Authorization': f'Bearer {self.bearer_token}'
        }

    def initiate_checkout(self, amount, currency, entity_id, user_details):
        """
        Calls HyperPay's /v1/checkouts to get a checkoutId.
        """
        url = f"{self.base_url}/v1/checkouts"
        
        # HyperPay requires amount to be a string with 2 decimal places
        data = {
            'entityId': entity_id,
            'amount': f"{amount:.2f}",
            'currency': currency,
            'paymentType': 'DB', # Debit
            'customer.email': user_details.get('email'),
            'billing.street1': user_details.get('address_line1'),
            'billing.city': user_details.get('city'),
            'billing.state': user_details.get('state', 'N/A'),
            'billing.country': user_details.get('country', 'SA'),
            'billing.postcode': user_details.get('postal_code'),
            'customer.givenName': user_details.get('first_name'),
            'customer.surname': user_details.get('last_name'),
        }
        
        try:
            response = requests.post(url, data=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"HyperPay initiate_checkout error: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response Content: {e.response.text}")
            return None

    def get_payment_status(self, checkout_id, entity_id):
        """
        Verify the transaction status using checkoutId.
        """
        url = f"{self.base_url}/v1/checkouts/{checkout_id}/payment"
        params = {
            'entityId': entity_id
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"HyperPay get_payment_status error: {e}")
            return None

class OmnifulService:
    def __init__(self):
        self.api_key = getattr(settings, 'OMNIFUL_API_KEY', '')
        self.base_url = "https://api.omniful.com/v1" # Placeholder, adjust if needed
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def create_order(self, order_payload):
        """
        Push the full order payload to Omniful.
        """
        url = f"{self.base_url}/orders"
        try:
            response = requests.post(url, json=order_payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Omniful create_order error: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response Content: {e.response.text}")
            raise e # Raise to allow Celery retry

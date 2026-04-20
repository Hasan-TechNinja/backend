from django.test import TestCase
from unittest.mock import patch
from account.serializers import SendOTPSerializer
from account.models import User


# Create your tests here.

from django.test import override_settings

@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
})
class SendOTPTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="12345678",
            password="password123"
        )

    @patch('account.serializers.send_otp_email.delay')
    def test_send_otp_queues_task(self, mock_delay):
        data = {"email": "test@example.com"}
        serializer = SendOTPSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        otp_obj = serializer.save()
        # serializer.save should call the Celery task queue
        mock_delay.assert_called_once()
        self.assertEqual(otp_obj.user, self.user)


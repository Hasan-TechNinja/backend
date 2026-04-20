"""
ASGI config for skincare project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skincare.settings")

# ✅ FIX: define this properly
django_asgi_app = get_asgi_application()


from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# your custom middleware
from notifications.middleware import JWTAuthMiddleware, ProtocolAcceptMiddleware
from notifications import routing


# application = ProtocolTypeRouter({
#     "http": django_asgi_app,

#     "websocket": AllowedHostsOriginValidator(
#         JWTAuthMiddleware(
#             ProtocolAcceptMiddleware(
#                 URLRouter(routing.websocket_urlpatterns)
#             )
#         ),
#     ),
# })


application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": JWTAuthMiddleware(
        ProtocolAcceptMiddleware(
            URLRouter(routing.websocket_urlpatterns)
        )
    ),
})
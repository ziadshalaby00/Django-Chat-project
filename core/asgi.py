"""
ASGI config for project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from .websocke_auth import CookieJWTAuthWebSocket

from chat.routing import websocket_urlpatterns as chat_ws

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socketdevto.settings')

combined_websocket_routes = [
    *chat_ws,
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": CookieJWTAuthWebSocket(
        URLRouter(combined_websocket_routes)
    )
})

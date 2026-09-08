"""
ASGI config for project project.
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socketdevto.settings')

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from .websocke_auth import CookieJWTAuthWebSocket

from chat.routing import websocket_urlpatterns as chat_ws
from message.routing import websocket_urlpatterns as chat_mes_ws


combined_websocket_routes = [
    *chat_ws,
    *chat_mes_ws,
]


application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": CookieJWTAuthWebSocket(
        URLRouter(combined_websocket_routes)
    ),
})
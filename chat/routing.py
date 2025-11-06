from django.urls import re_path
from .chat_consumers import ChatConsumer

websocket_urlpatterns = [
    re_path('ws/chat/', ChatConsumer.as_asgi()),
]
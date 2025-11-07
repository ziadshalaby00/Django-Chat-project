from django.urls import re_path
from .chat_mes_consumers import ChatMesConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat_messages/(?P<chat_id>\d+)/$', ChatMesConsumer.as_asgi()),
]
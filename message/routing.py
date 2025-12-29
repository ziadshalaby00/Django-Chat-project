from django.urls import re_path
from .chat_message_consumers import ChatMessageConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat_messages/(?P<chat_id>\d+)/$', ChatMessageConsumer.as_asgi()),
]
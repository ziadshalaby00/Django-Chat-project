from django.shortcuts import get_object_or_404
from message.models import Message
from chat.serializers import ChatSerializer
from chat.models import Chat
from django.core.exceptions import PermissionDenied

def get_reply_to_message(user, chat: Chat, reply_to_id: int):
    if not reply_to_id:
        return None
    
    if not chat.participants.filter(user=user).exists():
        raise PermissionDenied("User not a participant in this chat.")
    
    return get_object_or_404(Message, id=reply_to_id, chat=chat)

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from message.serializers import MessageSerializer

def broadcast_new_message(message, request):
    chat = message.chat
    message_data = MessageSerializer(message, context={"request": request}).data

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{chat.id}",
        {
            "type": "broadcast_new_message",
            "message_data": message_data
        }
    )

    return message_data
    
import json
from rest_framework.renderers import JSONRenderer

def notify_chat_participants(message):
    chat = message.chat
    participants = chat.participants.exclude(user=message.sender)

    # serialize بـ JSONRenderer عشان يطلع bytes
    chat_json = JSONRenderer().render(ChatSerializer(chat).data)
    # حول لـ dict
    chat_dict = json.loads(chat_json)

    channel_layer = get_channel_layer()
    for participant in participants:
        async_to_sync(channel_layer.group_send)(
            f"user_{participant.user.id}",
            {
                "type": "notify_chat_participants",
                "chat": chat_dict
            }
        )
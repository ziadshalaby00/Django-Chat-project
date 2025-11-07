from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from chat.models import Chat
from message.models import Message
from rest_framework.response import Response
from django.db import transaction
from .models import TextMessage
from message.serializers import MessageSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import status

# Create your views here.
class TextMessageAPIView(APIView):
    def post(self, request, chat_id):
        user = request.user

        chat = get_object_or_404(
            Chat,
            Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
        )

        content = request.data.get('content', '').strip()
        if not content:
            return Response(
                {'detail': 'Content cannot be empty.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            reply_to_obj = None
            reply_to_id = request.data.get("reply_to")

            if reply_to_id:
                reply_to_obj = get_object_or_404(
                    Message,
                    id=reply_to_id,
                    chat=chat
                )

            message = Message.objects.create(
                chat=chat,
                sender=user,
                type='text',
                reply_to=reply_to_obj,
            )
            
            TextMessage.objects.create(
                message=message,
                content=content
            )

        message_data = MessageSerializer(message).data

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_id}",
            {
                "type": "send_message",
                "message_data": message_data
            }
        )

        receiver = chat.user2 if user == chat.user1 else chat.user1
        async_to_sync(channel_layer.group_send)(
            f"user_{receiver.id}",
            { 'type': 'new_message_notification' }
        )

        return Response(message_data, status=status.HTTP_201_CREATED)

class UpdateTextMessageApiView(APIView):
    def patch(self, request, text_message_id):
        user = request.user
        text_message = get_object_or_404(TextMessage, id=text_message_id)
        
        if text_message.message.sender != user:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        new_content = request.data.get("content", "").strip()
        if not new_content:
            return Response({'detail': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

        text_message.content = new_content
        text_message.save()
        message_data = MessageSerializer(text_message.message).data
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{text_message.message.chat.id}",
            {
                "type": "message_updated",
                "message_data": message_data
            }
        )

        return Response(message_data, status=status.HTTP_200_OK)
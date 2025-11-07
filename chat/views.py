from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404
from message.models import Message

from .models import Chat
from .serializers import ChatSerializer

User = get_user_model()


class ChatAPIView(APIView):
    def get(self, request, chat_id=None):
        user = request.user

        queryset = Chat.objects.filter(
            Q(user1=user) | Q(user2=user)
        )

        serializer = ChatSerializer(
            queryset, 
            many=True,
            context={"request": request}
        )

        return Response({ "chats": serializer.data }, status=status.HTTP_200_OK)
    
    def post(self, request):
        data = request.data.copy()
        data["user1"] = request.user.id

        user1 = request.user.id
        user2 = data.get("user2")

        # Check existing chat
        existing_chat = Chat.objects.filter(
            Q(user1=user1, user2=user2) |
            Q(user1=user2, user2=user1)
        ).first()

        if existing_chat:
            serializer = ChatSerializer(existing_chat, context={"request": request})
            return Response({
                "detail": 'Chat already exists',
                "chat": serializer.data
            }, status=status.HTTP_200_OK)

        # Create new chat
        serializer = ChatSerializer(data=data, context={"request": request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        chat = serializer.save()

        # Send WebSocket event
        channel_layer = get_channel_layer()
        payload = {
            "type": "chat_created",
            "chat": serializer.data
        }

        async_to_sync(channel_layer.group_send)(
            f"user_{chat.user1.id}",
            payload
        )

        if chat.user1.id != chat.user2.id:
            async_to_sync(channel_layer.group_send)(
                f"user_{chat.user2.id}",
                payload
            )

        return Response({ "chat": serializer.data }, status=status.HTTP_201_CREATED)

    def delete(self, request, chat_id=None):
        if chat_id is None:
            return Response({"detail": "chat_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return Response({"detail": "Chat not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user not in [chat.user1, chat.user2]:
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        user1_id = chat.user1.id
        user2_id = chat.user2.id

        chat_id_deleted = chat.id

        chat.delete()

        channel_layer = get_channel_layer()
        payload = {
            "type": "chat_deleted",
            "chat_id": chat_id_deleted
        }

        async_to_sync(channel_layer.group_send)(
            f"user_{user1_id}",
            payload
        )
        if user1_id != user2_id:
            async_to_sync(channel_layer.group_send)(
                f"user_{user2_id}",
                payload
            )

        return Response({
            "detail": "Chat deleted",
            "chat_id": chat_id_deleted
        }, status=status.HTTP_200_OK)

class MarkChatReadApiView(APIView):
    def post(self, request, chat_id):
        user = request.user
        chat = get_object_or_404(
            Chat,
            Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
        )

        Message.objects.filter(chat=chat, isRead=False).exclude(sender=user).update(isRead=True)
        return Response({'detail': 'Messages marked as read.'}, status=status.HTTP_200_OK)
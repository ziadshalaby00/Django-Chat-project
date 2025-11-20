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
from .serializers import ChatSerializer, UserByUsernameSerializer

User = get_user_model()


class ChatAPIView(APIView):
    def get(self, request, chat_id=None):
        user = request.user

        queryset = Chat.objects.filter(
            Q(user1=user, user1_deleted_chat=False) |
            Q(user2=user, user2_deleted_chat=False)
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
            if request.user == existing_chat.user1 and existing_chat.user1_deleted_chat:
                existing_chat.user1_deleted_chat = False
                existing_chat.save()
            elif request.user == existing_chat.user2 and existing_chat.user2_deleted_chat:
                existing_chat.user2_deleted_chat = False
                existing_chat.save()

            serializer = ChatSerializer(existing_chat, context={"request": request})
            return Response({
                "detail": "Chat already exists",
                "chat": serializer.data
            }, status=status.HTTP_200_OK)

        # Check if user2 exists and is active
        try:
            other_user = User.objects.get(id=user2)
            if not other_user.is_active:
                return Response(
                    {"detail": "This user is deactivated and cannot receive chats."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {"detail": "User does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

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
            return Response({"detail": "Chat id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return Response({"detail": "Chat not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user not in [chat.user1, chat.user2]:
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        if request.user == chat.user1:
            chat.user1_deleted_chat = True
        else:
            chat.user2_deleted_chat = True

        chat.save()

        return Response({
            "detail": "Chat deleted",
            "chat_id": chat.id
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

class GetUserByUsername(APIView):
    def get(self, request):
        username = request.query_params.get('username', '').strip()

        if not username:
            return Response({
                'detail': 'Username is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username, is_active=True)
            data = UserByUsernameSerializer(user).data

        except User.DoesNotExist:
            return Response({
                "detail": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "user": data
        }, status=status.HTTP_200_OK)

from rest_framework.response import Response
from rest_framework import viewsets, status
from django.db.models import Q
from django.contrib.auth import get_user_model
from .serializers import ChatSerializer
from .models import Chat
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User = get_user_model()

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(Q(user1=user) | Q(user2=user))

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        # Copy request data safely
        data = request.data.copy()
        data["user1"] = request.user.id

        # ---- 1) Check if chat already exists (VERY IMPORTANT) ----
        user1 = request.user.id
        user2 = data.get("user2")

        existing_chat = Chat.objects.filter(
            Q(user1=user1, user2=user2) |
            Q(user1=user2, user2=user1)
        ).first()

        if existing_chat:
            # Return existing chat directly, do NOT create a new one
            serializer = self.get_serializer(existing_chat, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        # ---- 2) Create new chat ----
        serializer = self.get_serializer(data=data, context={'request': request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        chat = serializer.save()

        # ---- 3) Send WebSocket event to both users ----
        channel_layer = get_channel_layer()
        payload = {
            'type': 'chat.created',
            'chat': serializer.data
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

        return Response(serializer.data, status=201)

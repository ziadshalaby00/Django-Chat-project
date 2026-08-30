from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from chat.models import Chat
from django.db.models import Q
from .models import Message
from .serializers import MessageSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from chat.utils import created_after

class MessagePagination(PageNumberPagination):
    page_size = 15

class MessageAPIView(APIView):
    def get(self, request, chat_id):
        user = request.user

        chat = get_object_or_404(
            Chat,
            id=chat_id,
            participants__user=user,
            participants__deleted_chat=False
        )

        participant = get_object_or_404(chat.participants, user=user)

        messages = (
            Message.objects
            .filter(
                chat=chat,
                timestamp__gt=created_after(participant)
            )
            .select_related("sender")
            .order_by("-timestamp")
        )

        paginator = MessagePagination()
        paginated = paginator.paginate_queryset(messages, request)

        serializer = MessageSerializer(paginated, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

class DeleteMessageAPIView(APIView):
    def delete(self, request, message_id: int) -> Response:
        user = request.user
        message = get_object_or_404(Message, id=message_id, sender=user)
        chat = message.chat

        if not chat.participants.filter(user=user).exists():
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        chat_id = chat.id
        message.delete()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_id}",
            {
                "type": "message_deleted",
                "message_id": message_id
            }
        )

        return Response({
            "detail": 'Message deleted',
            "message_id": message_id
        }, status=status.HTTP_200_OK)
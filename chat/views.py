from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404
from message.models import Message

from django.utils import timezone
from django.db.models import Max
from django.db.models import Count

from .models import Chat
from .serializers import ChatSerializer, UserByUsernameSerializer

User = get_user_model()

from .utils import created_after

class ChatAPIView(APIView):
    def get(self, request, chat_id=None):
        user = request.user

        queryset = Chat.objects.filter(
            participants__user=user,
            participants__deleted_chat=False
        ).annotate(
            last_message_time=Max('messages__timestamp')
        ).order_by('-last_message_time').distinct()

        serializer = ChatSerializer(
            queryset, 
            many=True,
            context={"request": request}
        )

        return Response({"chats": serializer.data}, status=status.HTTP_200_OK)
    
    def post(self, request, chat_id=None):
        user1 = request.user.id
        user2 = request.data.get("user")
        
        if not user2:
            return Response({"detail": "user is required"}, status=400)

        # Check existing chat
        existing_chat = Chat.objects.annotate(
            num_participants=Count('participants'),
            participants_ids=Count(
                'participants', 
                filter=Q(participants__user__in=[user1, user2])
            )
        ).filter(
            num_participants=2,
            participants_ids=2
        ).first()

        if existing_chat:
            # Restore deleted_chat if needed
            participant = get_object_or_404(existing_chat.participants, user=request.user)
            if participant.deleted_chat:
                participant.deleted_chat = False
                participant.save()

            serializer = ChatSerializer(existing_chat, context={"request": request})
            return Response({
                "detail": "Chat already exists",
                "chat": serializer.data
            }, status=status.HTTP_200_OK)

        # Check if user2 exists and is active
        get_object_or_404(User, id=user2)

        # Create new chat
        serializer = ChatSerializer(data={"user_ids": [user1, user2]}, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        chat = serializer.save()

        # Send WebSocket event
        channel_layer = get_channel_layer()
        payload = {
            "type": "chat_created",
            "chat": serializer.data
        }

        for participant in chat.participants.all():
            async_to_sync(channel_layer.group_send)(
                f"user_{participant.user.id}",
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

        if not chat.participants.filter(user=request.user).exists():
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        participant = get_object_or_404(chat.participants, user=request.user)
        participant.deleted_chat = True
        participant.deleted_at = timezone.now()
        participant.save()

        return Response({
            "detail": "Chat deleted",
            "chat_id": chat.id
        }, status=status.HTTP_200_OK)

class MarkChatReadApiView(APIView):
    def post(self, request, chat_id):
        user = request.user

        chat = get_object_or_404(
            Chat,
            id=chat_id,
            participants__user=user
        )

        participant = get_object_or_404(chat.participants, user=user)
        
        Message.objects.filter(
            chat=chat,
            isRead=False,
            timestamp__gt=created_after(participant)
        ).exclude(sender=user).update(isRead=True)

        return Response({'detail': 'Messages marked as read.'}, status=status.HTTP_200_OK)

class GetUserByUsername(APIView):
    def get(self, request):
        username = request.query_params.get('username', '').strip()

        if not username:
            return Response({
                'detail': 'Username is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
            data = UserByUsernameSerializer(user).data

        except User.DoesNotExist:
            return Response({
                "detail": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "user": data
        }, status=status.HTTP_200_OK)

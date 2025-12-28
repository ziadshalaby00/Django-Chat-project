from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Chat, ChatParticipant
from auth_app.serializers import ChatUserSerializer

from django.utils import timezone
from datetime import datetime

User = get_user_model()


class ChatParticipantSerializer(serializers.ModelSerializer):
    user_info = ChatUserSerializer(source='user', read_only=True)

    class Meta:
        model = ChatParticipant
        fields = [
            'user_info',
        ]

class ChatSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    # create-only fields
    user_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=User.objects.all()),
        write_only=True
    )

    class Meta:
        model = Chat
        fields = [
            'id',
            'participants',
            'user_ids',   # for create
            'created_at',
            'unread_count',
        ]

    def get_participants(self, obj):
        participants = obj.participants.all()
        return ChatParticipantSerializer(participants, many=True, context=self.context).data

    def get_unread_count(self, obj):
        if obj.messages.count() == 0:
            return 0
        
        request = self.context.get('request')
        if not request:
            return 0

        user = request.user
        participant = obj.participants.filter(user=user).first()
        if not participant:
            return 0

        created_after = participant.deleted_at or timezone.make_aware(datetime.min)
        return obj.messages.filter(
            isRead=False, 
            timestamp__gt=(created_after)
        ).exclude(sender=user).count()

    def create(self, validated_data):
        user_ids = validated_data.pop('user_ids')
        chat = Chat.objects.create(**validated_data)

        participants = [
            ChatParticipant(chat=chat, user=user)
            for user in user_ids
        ]
        ChatParticipant.objects.bulk_create(participants)
        return chat


class UserByUsernameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'fullname',
            'username',
        ]

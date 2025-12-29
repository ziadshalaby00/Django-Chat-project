from rest_framework import serializers
from .models import Message
from auth_app.serializers import ChatUserSerializer
from audio_message.serializers import AudioMessageSerializer
from file_message.serializers import FileMessageSerializer
from text_message.serializers import TextMessageSerializer

class ReplyMessageSerializer(serializers.ModelSerializer):
    sender = ChatUserSerializer(read_only=True)
    audio_message = AudioMessageSerializer(read_only=True)
    file_message = FileMessageSerializer(read_only=True)
    text_message = TextMessageSerializer(read_only=True)

    class Meta:
        model = Message
        exclude = ['reply_to']


class MessageSerializer(serializers.ModelSerializer):
    sender = ChatUserSerializer(read_only=True)
    reply_to = serializers.SerializerMethodField()

    audio_message = AudioMessageSerializer(read_only=True)
    file_message = FileMessageSerializer(read_only=True)
    text_message = TextMessageSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 
            'chat', 
            'sender', 
            'type', 
            'timestamp',
            'reply_to',
            'audio_message',
            'file_message',
            'text_message'
        ]

    def get_reply_to(self, obj):
        if obj.reply_to:
            return ReplyMessageSerializer(obj.reply_to).data
        return None

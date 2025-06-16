from django.contrib.auth.models import User
from rest_framework import serializers
from .models import *

class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class ChatSerializer(serializers.ModelSerializer):
    user1_info = UserSerializer(source='user1', read_only=True)
    user2_info = UserSerializer(source='user2', read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = "__all__"

    def get_unread_count(self, obj):
        return obj.messages.filter(isRead=False).exclude(sender=self.context.get('user')).count()

class AudioMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioMessage
        fields = ['audio_file', 'audio_duration']

class FileMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileMessage
        fields = ['file', 'file_name', 'file_size', 'file_type']

class ReplyMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    audio = AudioMessageSerializer(read_only=True)
    file_data = FileMessageSerializer(read_only=True)
    class Meta:
        model = Message
        exclude = ['reply_to']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    reply_to = serializers.SerializerMethodField()
    audio = AudioMessageSerializer(read_only=True)
    file_data = FileMessageSerializer(read_only=True)

    class Meta:
        model = Message
        fields = '__all__'

    def get_reply_to(self, obj):
        if obj.reply_to:
            return ReplyMessageSerializer(obj.reply_to).data
        return None
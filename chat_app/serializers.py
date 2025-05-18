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
    user1_username = serializers.SerializerMethodField()
    user2_username = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = '__all__'

    def get_user1_username(self, obj):
        return obj.user1.username if obj.user1 else None

    def get_user2_username(self, obj):
        return obj.user2.username if obj.user2 else None

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
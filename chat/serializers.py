from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Chat
from auth_app.serializers import ChatUserSerializer

User = get_user_model()


class ChatSerializer(serializers.ModelSerializer):
    user1_info = ChatUserSerializer(source='user1', read_only=True)
    user2_info = ChatUserSerializer(source='user2', read_only=True)
    
    # create-only fields 
    user1 = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True) 
    user2 = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            'id',
            'user1',
            'user2',
            
            'user1_deleted_chat',
            'user2_deleted_chat',
            
            'user1_info',
            'user2_info',
            
            'created_at',
            'unread_count',
        ]

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request:
            return 0

        user = request.user
        return obj.messages.filter(isRead=False).exclude(sender=user).count()

class UserByUsernameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'fullname',
            'username',
        ]

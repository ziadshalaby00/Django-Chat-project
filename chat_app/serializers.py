from django.contrib.auth.models import User
from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    
class ChatSerializer(serializers.ModelSerializer):
    user1_username = serializers.SerializerMethodField()
    user2_username = serializers.SerializerMethodField()
    class Meta:
        model = Chat
        fields = '__all__'
    
    def get_user1_username(self, obj):
        # إرجاع username الخاص بـ user1
        return obj.user1.username if obj.user1 else None

    def get_user2_username(self, obj):
        # إرجاع username الخاص بـ user2
        return obj.user2.username if obj.user2 else None
        
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
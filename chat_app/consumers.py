# chat/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from .serializers import *
import json
from django.shortcuts import get_object_or_404

class ChatConsumerMes(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.user = self.scope["user"]
        self.type = None
        self.file_name = None
        
        if self.user is None or self.user.is_anonymous:
            await self.close()
            return

        # تحقق أن المستخدم جزء من المحادثة
        if not await self.is_user_in_chat(self.chat_id, self.user):
            await self.close()
            return

        self.room_group_name = f'chat_{self.chat_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except Exception:
            pass
        
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def is_user_in_chat(self, chat_id, user):
        try:
            chat = Chat.objects.get(id=chat_id)
            return user == chat.user1 or user == chat.user2
        except Chat.DoesNotExist:
            return False
        
    async def receive(self, text_data=None, bytes_data=None):
        obj = None

        if text_data:
            data = json.loads(text_data)
            message = data.get('message', None)
            if message:
                obj = await self.save_message(self.chat_id, self.user, message)
            
        if obj:
            serialized_data = MessageSerializer(obj).data
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'data': serialized_data,
                }
            )
            
    @database_sync_to_async
    def save_message(self, chat_id, user, content):
        chat = get_object_or_404(Chat, id=chat_id)
        return Message.objects.create(
            chat=chat, 
            sender=user, 
            content=content, 
            type='message'
        )
        
    async def message_updated(self, event):
        await self.send(text_data=json.dumps({
            "type": "message.updated",
            "data": event["data"]
        }))
    
    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            "type": "message.deleted",
            "data": event["data"]
        }))


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if self.user is None or self.user.is_anonymous:
            await self.close()
            return

        self.group_name = f"user_{self.user.id}"
        
        await self.channel_layer.group_add(
            self.group_name, 
            self.channel_name
        )
        await self.accept()

        # إرسال المحادثات الخاصة بالمستخدم
        chats = await self.get_user_chats()
        await self.send(text_data=json.dumps({
            'type': 'initial_chats',
            'chats': chats
        }))

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        except Exception:
            pass

    async def receive(self, text_data):
        pass

    async def chat_created(self, event):
        chat = event['chat']
        await self.send(text_data=json.dumps({
            'type': 'chat_created',
            'chat': chat
        }))

    @database_sync_to_async
    def get_user_chats(self):
        chats = (Chat.objects.filter(user1=self.user) | Chat.objects.filter(user2=self.user)).order_by('-created_at')
        serializer = ChatSerializer(chats, many=True)
        print(serializer.data)
        return serializer.data
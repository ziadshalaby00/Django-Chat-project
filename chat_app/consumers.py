# chat/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from .serializers import *
import json
from django.shortcuts import get_object_or_404
from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class ChatConsumerMes(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.user = self.scope["user"]
        
        if self.user is None or self.user.is_anonymous:
            await self.close()
            return

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
        
    async def receive(self, text_data=None):
        obj = None

        if text_data:
            data = json.loads(text_data)
            message = data.get('message', None)
            reply_to = data.get('reply_to', None)
            
            if not message or not message.strip():
                return
            
            obj = await self.save_message(self.chat_id, self.user, message, reply_to)
            
        if obj:
            serialized_data = await self.serialize_message(obj)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'data': serialized_data,
                }
            )
        
        channel_layer = get_channel_layer()
        receiver = await self.get_receiver(obj)
        await channel_layer.group_send(
            f"user_{receiver.id}", 
            {
                'type': 'new_message_notification',
                'message': serialized_data
            }
        )

    @database_sync_to_async
    def get_receiver(self, obj):
        chat = obj.chat
        sender = obj.sender

        user1 = chat.user1
        user2 = chat.user2

        return user2 if sender == user1 else user1

    @database_sync_to_async
    def save_message(self, chat_id, user, content, reply_to_id):
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return None
        
        if reply_to_id and str(reply_to_id).isdigit():
            reply_to_id = int(reply_to_id)
            reply_to_obj = Message.objects.filter(id=reply_to_id).first()
            if reply_to_obj and reply_to_obj.chat_id != chat.id:
                return None
        else:
            reply_to_obj = None
        
        return Message.objects.create(
            chat=chat, 
            sender=user, 
            content=content, 
            type='message',
            reply_to=reply_to_obj,
        )
        
    @database_sync_to_async
    def serialize_message(self, obj):
        return MessageSerializer(obj).data
        
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
    
    async def new_message_notification(self, event):
        message_data = event['message']

        await self.send(text_data=json.dumps({
            'type': 'new_message_notification',
            'message': message_data
        }))

    @database_sync_to_async
    def get_user_chats(self):
        chats = (Chat.objects.filter(user1=self.user) | Chat.objects.filter(user2=self.user)).order_by('-created_at')
        serializer_data = [ChatSerializer(chat, context={'user': self.user}).data for chat in chats]
        return serializer_data
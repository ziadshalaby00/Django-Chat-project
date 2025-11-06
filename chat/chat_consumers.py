from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat
from .serializers import ChatSerializer
from django.db.models import Q

class ChatConsumer(AsyncJsonWebsocketConsumer):
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
        await self.send_json({
            'type': 'initial_chats',
            'chats': chats
        })

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
        print(chat)

        if self.user.id not in (chat['user1_info']['id'], chat['user2_info']['id']):
            return

        await self.send_json({
            'type': 'chat_created',
            'chat': chat
        })
    
    async def new_message_notification(self, event):
        message_data = event['message']

        await self.send_json({
            'type': 'new_message_notification',
            'message': message_data
        })

    @database_sync_to_async
    def get_user_chats(self):
        chats = Chat.objects.filter(
            Q(user1=self.user) | Q(user2=self.user)
        ).select_related("user1", "user2").order_by('-created_at')

        return [ChatSerializer(chat, context={'user': self.user}).data for chat in chats]

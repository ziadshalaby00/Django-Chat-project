from channels.generic.websocket import AsyncJsonWebsocketConsumer
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

        if self.user.id not in [p['user_info']['id'] for p in chat['participants']]:
            return

        await self.send_json({
            'type': 'chat_created',
            'chat': chat
        })
    
    async def new_message_notification(self, event):
        await self.send_json({ 'type': 'new_message_notification' })

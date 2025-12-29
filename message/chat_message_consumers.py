# chat/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat

class ChatMessageConsumer(AsyncJsonWebsocketConsumer):
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

    async def broadcast_new_message(self, event):
        await self.send_json({
            "type": "broadcast_new_message",
            "message_data": event['message_data']
        })

    async def receive(self, text_data=None):
        pass

    @database_sync_to_async
    def is_user_in_chat(self, chat_id, user):
        try:
            return Chat.objects.filter(
                id=chat_id,
                participants__user=user
            ).exists()
        except Chat.DoesNotExist:
            return False

    async def message_deleted(self, event):
        await self.send_json({
            "type": "message_deleted",
            "message_id": event["message_id"]
        })

    async def message_updated(self, event):
        await self.send_json({
            "type": "message_updated",
            "message_data": event["message_data"]
        })
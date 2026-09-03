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

    async def receive_json(self, content, **kwargs):
        message_type = content.get('type')

        call_handlers = {
            'call.offer': self.handle_call_offer,
            'call.answer': self.handle_call_answer,
            'call.ice_candidate': self.handle_call_ice_candidate,
            'call.reject': self.handle_call_reject,
            'call.end': self.handle_call_end,
        }

        handler = call_handlers.get(message_type)

        if handler:
            await handler(content)

    # ==================== Call Signaling ==================== #

    async def _relay_to_user(self, to_user_id, payload):
        if not to_user_id:
            return

        await self.channel_layer.group_send(
            f"user_{to_user_id}",
            {
                'type': 'call_signal',
                'payload': payload,
            }
        )

    async def handle_call_offer(self, content):
        await self._relay_to_user(
            content.get('to_user_id'),
            {
                'type': 'call.offer',
                'sdp': content.get('sdp'),
                'call_type': content.get('call_type', 'video'),
                'chat_id': content.get('chat_id'),
                'from_user_id': self.user.id,
            },
        )

    async def handle_call_answer(self, content):
        await self._relay_to_user(
            content.get('to_user_id'),
            {
                'type': 'call.answer',
                'sdp': content.get('sdp'),
                'from_user_id': self.user.id,
            },
        )

    async def handle_call_ice_candidate(self, content):
        await self._relay_to_user(
            content.get('to_user_id'),
            {
                'type': 'call.ice_candidate',
                'candidate': content.get('candidate'),
                'from_user_id': self.user.id,
            },
        )

    async def handle_call_reject(self, content):
        await self._relay_to_user(
            content.get('to_user_id'),
            {
                'type': 'call.reject',
                'from_user_id': self.user.id,
            },
        )

    async def handle_call_end(self, content):
        await self._relay_to_user(
            content.get('to_user_id'),
            {
                'type': 'call.end',
                'from_user_id': self.user.id,
            },
        )

    async def call_signal(self, event):
        await self.send_json(event['payload'])

    # ==================== Existing Handlers ==================== #

    async def chat_created(self, event):
        chat = event['chat']

        if self.user.id not in [p['user_info']['id'] for p in chat['participants']]:
            return

        await self.send_json({
            'type': 'chat_created',
            'chat': chat
        })

    async def notify_chat_participants(self, event):
        chat = event['chat']

        if self.user.id not in [p['user_info']['id'] for p in chat['participants']]:
            return

        await self.send_json({
            'type': 'new_message_notification',
            'chat_id': chat['id']
        })
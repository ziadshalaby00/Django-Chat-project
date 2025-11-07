from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from django.db.models import Q
import magic
import time, os, subprocess, tempfile
from message.models import Message
from .models import AudioMessage
from django.core.files import File
from mutagen.mp3 import MP3
from message.serializers import MessageSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db import transaction
from chat.models import Chat
from rest_framework import status

class UploadAudioAPIView(APIView):
    def post(self, request, chat_id):
        user = request.user
        
        chat = get_object_or_404(
            Chat, 
            Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
        )
        raw_audio = request.FILES.get('audio')

        if not raw_audio:
            return Response({"detail": "Audio file is required."}, status=status.HTTP_400_BAD_REQUEST)

        mime_type = magic.from_buffer(raw_audio.read(2048), mime=True)
        raw_audio.seek(0)

        if mime_type not in ["audio/webm", "video/webm"]:
            return Response({"detail": "Only webm audio is allowed."}, status=status.HTTP_400_BAD_REQUEST)

        temp_input = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
        temp_output_path = temp_input.name.replace(".webm", ".mp3")

        try:
            for chunk in raw_audio.chunks():
                temp_input.write(chunk)
            temp_input.close()

            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", temp_input.name,
                    "-codec:a", "libmp3lame",
                    "-qscale:a", "5",
                    temp_output_path
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15
            )

            if result.returncode != 0:
                return Response({"detail": "Audio conversion failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            mp3_info = MP3(temp_output_path)
            duration = mp3_info.info.length

            with transaction.atomic():

                reply_to_obj = None
                reply_to_id = request.data.get("reply_to")

                if reply_to_id:
                    reply_to_obj = get_object_or_404(
                        Message,
                        id=reply_to_id,
                        chat=chat
                    )

                message = Message.objects.create(
                    chat=chat,
                    sender=user,
                    type="audio",
                    reply_to=reply_to_obj
                )

                filename = f"{user.id}_{chat.id}_{int(time.time())}.mp3"

                with open(temp_output_path, "rb") as f:
                    AudioMessage.objects.create(
                        message=message,
                        audio_file=File(f, name=filename),
                        audio_duration=duration
                    )

        finally:
            if os.path.exists(temp_input.name):
                os.remove(temp_input.name)
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)

        message_data = MessageSerializer(message).data

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_id}",
            {
                "type": "send_message",
                "message_data": message_data
            }
        )

        receiver = chat.user2 if user == chat.user1 else chat.user1
        async_to_sync(channel_layer.group_send)(
            f"user_{receiver.id}",
            { "type": "new_message_notification" }
        )

        return Response(message_data, status=status.HTTP_201_CREATED)
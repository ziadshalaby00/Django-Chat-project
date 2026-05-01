from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
import magic
import uuid
import os, subprocess, tempfile
from message.models import Message
from .models import AudioMessage
from django.core.files import File
from mutagen.mp3 import MP3
from django.db import transaction
from chat.models import Chat
from rest_framework import status
from message.utils import (
    get_reply_to_message,
    broadcast_new_message,
    notify_chat_participants
)

class UploadAudioAPIView(APIView):
    def post(self, request, chat_id):
        user = request.user
        
        chat = get_object_or_404(
            Chat, 
            id=chat_id,
            participants__user=user
        )

        raw_audio = request.FILES.get('audio')
        if not raw_audio:
            return Response({"detail": "Audio file is required."}, status=status.HTTP_400_BAD_REQUEST)

        mime_type = magic.from_buffer(raw_audio.read(2048), mime=True)
        raw_audio.seek(0)

        if mime_type not in ["audio/webm", "video/webm"]:
            return Response({"detail": "Only webm audio is allowed."}, status=status.HTTP_400_BAD_REQUEST)

        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
        if raw_audio.size > MAX_FILE_SIZE:
            return Response(
                {"detail": "Audio file too large"},
                status=status.HTTP_400_BAD_REQUEST
            )

        temp_input = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
        temp_output_path = temp_input.name.replace(".webm", ".mp3")

        try:
            for chunk in raw_audio.chunks():
                temp_input.write(chunk)
            temp_input.close()

            result = subprocess.run(
                [
                    "ffmpeg",
                    "-nostdin",
                    "-y",
                    "-loglevel", "error",
                    "-i", temp_input.name,
                    "-codec:a", "libmp3lame",
                    "-b:a", "128k",
                    temp_output_path
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30
            )

            if result.returncode != 0:
                return Response({
                    "detail": "Unable to process audio. Please try recording again."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            mp3_info = MP3(temp_output_path)
            duration = mp3_info.info.length
            
            MAX_AUDIO_DURATION_SECONDS = 60 * 60  # 1 hour
            if duration > MAX_AUDIO_DURATION_SECONDS:
                return Response(
                    {"detail": "Audio is too long"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                reply_to_id = request.data.get("reply_to")
                reply_to_obj = get_reply_to_message(user, chat, reply_to_id)

                message = Message.objects.create(
                    chat=chat,
                    sender=user,
                    type="audio",
                    reply_to=reply_to_obj
                )

                filename = f"{uuid.uuid4().hex}.mp3"
                with open(temp_output_path, "rb") as f:
                    AudioMessage.objects.create(
                        message=message,
                        audio_file=File(f, name=filename),
                        audio_duration=duration
                    )
                    
                message_data = broadcast_new_message(message, request)
                notify_chat_participants(message)

        finally:
            if os.path.exists(temp_input.name):
                os.remove(temp_input.name)
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)

        return Response(message_data, status=status.HTTP_201_CREATED)
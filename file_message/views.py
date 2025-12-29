from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from chat.models import Chat
from message.models import Message
from .models import FileMessage
from django.db import transaction
import uuid
import os
import mimetypes
from .validators import validate_file_upload
from rest_framework import status
from message.utils import (
    get_reply_to_message,
    broadcast_new_message,
    notify_chat_participants
)

class UploadFileAPIView(APIView):
    def post(self, request, chat_id):
        user = request.user

        chat = get_object_or_404(
            Chat, 
            id=chat_id,
            participants__user=user
        )

        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'detail': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        error = validate_file_upload(uploaded_file)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            reply_to_id = request.data.get("reply_to")
            reply_to_obj = get_reply_to_message(user, chat, reply_to_id)

            message = Message.objects.create(
                chat=chat,
                sender=user,
                type='file',
                reply_to=reply_to_obj,
            )

            base_name = os.path.basename(uploaded_file.name).replace(" ", "_")
            base, ext = os.path.splitext(base_name)

            filename = f"{uuid.uuid4().hex}_{base}{ext}"
            file_size = uploaded_file.size

            file_type, _ = mimetypes.guess_type(uploaded_file.name)
            if not file_type:
                file_type = uploaded_file.content_type or ext.lstrip('.')

            uploaded_file.name = filename
            FileMessage.objects.create(
                message=message,
                file=uploaded_file,
                file_name=filename,
                file_size=file_size,
                file_type=file_type,
            )

            message_data = broadcast_new_message(message)
            notify_chat_participants(message)
        return Response(message_data, status=status.HTTP_201_CREATED)

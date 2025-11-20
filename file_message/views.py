from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from message.serializers import MessageSerializer
from chat.models import Chat
from message.models import Message
from .models import FileMessage
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Q
from django.db import transaction
import os
import time
import mimetypes
from .validators import validate_file_upload
from rest_framework import status
from message.utils import (
    can_send_message, 
    get_reply_to_message,
    send_new_message_notification
)

class UploadFileAPIView(APIView):
    def post(self, request, chat_id):
        user = request.user

        chat = get_object_or_404(
            Chat,
            Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
        )
        
        allowed, reason = can_send_message(user, chat)
        if not allowed:
            return Response({"detail": reason}, status=400)

        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'detail': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        error = validate_file_upload(uploaded_file)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            reply_to_id = request.data.get("reply_to")
            reply_to_obj = get_reply_to_message(chat, reply_to_id)

            message = Message.objects.create(
                chat=chat,
                sender=user,
                type='file',
                reply_to=reply_to_obj,
            )

            base_name = os.path.basename(uploaded_file.name).replace(" ", "_")
            base, ext = os.path.splitext(base_name)

            filename = f"{user.id}_{chat.id}_{int(time.time())}_{base}{ext}"
            file_size = uploaded_file.size

            file_type, _ = mimetypes.guess_type(uploaded_file.name)
            if not file_type:
                file_type = uploaded_file.content_type or ext.lstrip('.')

            FileMessage.objects.create(
                message=message,
                file=uploaded_file,
                file_name=filename,
                file_size=file_size,
                file_type=file_type,
            )

        message_data = send_new_message_notification(message)
        return Response(message_data, status=status.HTTP_201_CREATED)

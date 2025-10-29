from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .serializers import *
from rest_framework import viewsets, permissions
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time, os, subprocess, tempfile
from django.core.files.base import ContentFile
import magic
from .validators import *
from django.db.models import Q

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

import mimetypes
from mutagen.mp3 import MP3
# Create your views here.

class getUser(APIView):
    def get(self, request):
        username = request.GET.get("username")
        user = None
        
        if username:
            user = get_object_or_404(User, username=username)
        else:
            user = get_object_or_404(User, id=request.user.id)
            
        user = UserSerializer(user)
        return Response({
            "user": user.data
        }, status=status.HTTP_200_OK)

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(user1=user) | Chat.objects.filter(user2=user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer_data = [self.get_serializer(chat, context={'user': request.user}).data for chat in queryset]
        return Response(serializer_data)

    def create(self, request, *args, **kwargs):
        request.data["user1"] = request.user.id
        chat_seri = self.get_serializer(data=request.data, context={'user': request.user})

        if chat_seri.is_valid():
            chat = chat_seri.save()

            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                f"user_{chat.user1.id}",
                {
                    'type': 'chat.created',
                    'chat': chat_seri.data
                }
            )

            if chat.user1.id != chat.user2.id:
                async_to_sync(channel_layer.group_send)(
                    f"user_{chat.user2.id}",
                    {
                        'type': 'chat.created',
                        'chat': chat_seri.data
                    }
                )

            return Response(chat_seri.data, status=201)
        else:
            return Response(chat_seri.errors, status=400)

class MessageAPIView(APIView):
    def get(self, request, chat_id):
        user = request.user
        chat = get_object_or_404(Chat, Q(id=chat_id) & (Q(user1=user) | Q(user2=user)))

        messages = Message.objects.filter(chat=chat).order_by('timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

class UploadAudioAPIView(APIView):
    def post(self, request, chat_id):
        user = request.user
        chat = get_object_or_404(Chat, Q(id=chat_id) & (Q(user1=user) | Q(user2=user)))
        raw_audio = request.FILES.get('audio')

        if not raw_audio:
            return Response({'error': 'Audio file is required.'}, status=400)

        mime_type = magic.from_buffer(raw_audio.read(1024), mime=True)
        raw_audio.seek(0)
        if mime_type != "video/webm":
            return Response({'error': 'Only webm audio allowed.'}, status=400)

        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_input:
            for chunk in raw_audio.chunks():
                temp_input.write(chunk)
            input_path = temp_input.name

        output_path = input_path.replace(".webm", ".mp3")

        result = subprocess.run([
            "ffmpeg", "-y",
            "-i", input_path,
            "-codec:a", "libmp3lame",
            "-qscale:a", "5",
            output_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if result.returncode != 0:
            os.remove(input_path)
            return Response({'error': 'Audio conversion failed'}, status=500)

        with open(output_path, "rb") as f:
            mp3_data = f.read()

        reply_to_id = request.data.get('reply_to')
        if reply_to_id and str(reply_to_id).isdigit():
            reply_to_id = int(reply_to_id)
            reply_to_obj = Message.objects.filter(id=reply_to_id).first()
            if reply_to_obj and reply_to_obj.chat_id != chat.id:
                return Response({'error': 'Invalid reply target.'}, status=400)
        else:
            reply_to_obj = None
        
        message = Message.objects.create(
            chat=chat,
            sender=user,
            type='audio',
            reply_to=reply_to_obj,
        )
        
        filename = f"{user.id}_{chat.id}_{int(time.time())}.mp3"
        
        audio = MP3(output_path)
        duration = audio.info.length

        AudioMessage.objects.create(
            message=message,
            audio_file=ContentFile(mp3_data, name=filename),
            audio_duration=duration
        )

        os.remove(input_path)
        os.remove(output_path)

        message_data = MessageSerializer(message).data

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_id}",
            {
                "type": "chat_message",
                "data": message_data
            }
        )
        
        receiver = message.chat.user1 if message.sender != message.chat.user1 else message.chat.user2
        async_to_sync(channel_layer.group_send)(
            f"user_{receiver.id}", 
            {
                'type': 'new_message_notification',
                'message': message_data
            }
        )
        
        return Response(message_data, status=201)

class UploadFileAPIView(APIView):
    def post(self, request, chat_id):
        user = request.user
        chat = get_object_or_404(Chat, Q(id=chat_id) & (Q(user1=user) | Q(user2=user)))
        
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'error': 'No file uploaded'}, status=400)

        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)

        error = validate_file_upload(file_bytes)
        if error:
            return Response({'error': error}, status=400)

        reply_to_id = request.data.get('reply_to')
        if reply_to_id and str(reply_to_id).isdigit():
            reply_to_id = int(reply_to_id)
            reply_to_obj = Message.objects.filter(id=reply_to_id).first()
            if reply_to_obj and reply_to_obj.chat_id != chat.id:
                return Response({'error': 'Invalid reply target.'}, status=400)
        else:
            reply_to_obj = None

        message = Message.objects.create(
            chat=chat,
            sender=user,
            type='file',
            reply_to=reply_to_obj,
        )

        base, ext = os.path.splitext(uploaded_file.name)
        filename = f"{user.id}_{chat.id}_{int(time.time())}_{base}{ext}"
        file_size = uploaded_file.size

        file_type, _ = mimetypes.guess_type(uploaded_file.name)

        if not file_type:
            file_type = ext.lstrip('.')

        FileMessage.objects.create(
            message=message,
            file=ContentFile(file_bytes, name=filename),
            file_name=filename,
            file_size=file_size,
            file_type=file_type,
        )

        message_data = MessageSerializer(message).data

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_id}",
            {
                "type": "chat_message",
                "data": message_data
            }
        )
        
        receiver = message.chat.user1 if message.sender != message.chat.user1 else message.chat.user2
        async_to_sync(channel_layer.group_send)(
            f"user_{receiver.id}", 
            {
                'type': 'new_message_notification',
                'message': message_data
            }
        )
        
        return Response(message_data, status=201)
    
class UpdateMessageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id, sender=user)

        if message.type != 'message':
            return Response({'error': 'Only text messages can be edited.'}, status=400)

        new_content = request.data.get("content", "").strip()
        if not new_content:
            return Response({'error': 'Content is required'}, status=400)

        message.content = new_content
        message.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{message.chat.id}",
            {
                "type": "message.updated",
                "data": MessageSerializer(message).data
            }
        )

        return Response(MessageSerializer(message).data, status=200)

class DeleteMessageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, message_id: int) -> Response:
        user = request.user
        message = get_object_or_404(Message, id=message_id, sender=user)
        chat_id = message.chat.id
        serialized_data = MessageSerializer(message).data

        message.delete()

        # إرسال إشعار بالحذف
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_id}",
            {
                "type": "message.deleted",
                "data": serialized_data
            }
        )

        return Response({'detail': 'Message deleted'}, status=200)

# * ##################################################################################

class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        refresh_token = response.data.get('refresh')
        response.data.pop('refresh')
        
        response.set_cookie(
            key='refresh',
            value=refresh_token,
            
            httponly=settings.HTTPONLY,
            secure=settings.SECURE,
            samesite=settings.SAMESITE,
            path=settings.PATH,
            
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        )
        return response

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh')
        
        if refresh_token is None:
            return Response({'detail': 'Refresh token not found in cookies'}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = self.get_serializer(data={'refresh': refresh_token})
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            response = Response({'detail': 'Invalid or expired refresh token'}, status=status.HTTP_401_UNAUTHORIZED)
            return response

        access_token = serializer.validated_data.get('access')

        old_refresh = RefreshToken(refresh_token)
        user_id = old_refresh["user_id"]
        try:
            user = User.objects.get(id=user_id)
        except Exception:
            response = Response({'detail': 'User Not Found'}, status=status.HTTP_401_UNAUTHORIZED)
            return response
        
        new_refresh = RefreshToken.for_user(user)
        
        response = Response({
            'access': access_token,
        })
      
        response.set_cookie(
            key='refresh',
            value=str(new_refresh),
            httponly=settings.HTTPONLY,
            secure=settings.SECURE,
            samesite=settings.SAMESITE,
            path=settings.PATH,
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        )
        return response

class logout(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        response = Response({
            'success': "Logged out successfully"
        })
        response.delete_cookie(
            key='refresh',
            samesite=settings.SAMESITE,
            path=settings.PATH,
        )
        return response

# * ##################################################################################

class ChatNotificationsView(APIView):
    def post(self, request, chat_id):
        user = request.user
        chat = get_object_or_404(Chat, id=chat_id)

        if chat.user1 != user and chat.user2 != user:
            return Response({'detail': 'Access denied.'}, status=403)

        Message.objects.filter(chat=chat, isRead=False).exclude(sender=user).update(isRead=True)
        return Response({'detail': 'Messages marked as read.'}, status=200)


class getUsers(APIView):
    def get(self, request):
        users = User.objects.all()
        allUser = UserSerializer(users, many=True)
        
        return Response({
            "users": allUser.data
        })
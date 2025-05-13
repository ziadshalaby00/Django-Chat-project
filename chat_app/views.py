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

    def create(self, request, *args, **kwargs):
        request.data["user1"] = request.user.id
        chat_seri = self.get_serializer(data=request.data)

        if chat_seri.is_valid():
            chat = chat_seri.save()

            channel_layer = get_channel_layer()
            
            async_to_sync(channel_layer.group_send)(
                f"user_{chat.user1.id}",
                {
                    'type': 'chat.created',
                    'chat': ChatSerializer(chat).data
                }
            )

            async_to_sync(channel_layer.group_send)(
                f"user_{chat.user2.id}",
                {
                    'type': 'chat.created',
                    'chat': ChatSerializer(chat).data
                }
            )

            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)

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

        subprocess.run([
            "ffmpeg", "-y",
            "-i", input_path,
            "-codec:a", "libmp3lame",
            "-qscale:a", "5",
            output_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        with open(output_path, "rb") as f:
            mp3_data = f.read()


        message = Message.objects.create(
            chat=chat,
            sender=user,
            type='audio'
        )
        
        filename = f"{user.id}_{chat.id}_{int(time.time())}.mp3"
        message.audio_file.save(filename, ContentFile(mp3_data))

        os.remove(input_path)
        os.remove(output_path)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_id}",
            {
                "type": "chat_message",
                "data": MessageSerializer(message).data
            }
        )
        
        return Response(MessageSerializer(message).data, status=201)


class UploadFileAPIView(APIView):
    def post(self, request, chat_id):
        user = request.user
        chat = get_object_or_404(Chat, Q(id=chat_id) & (Q(user1=user) | Q(user2=user)))
        
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'error': 'No file uploaded'}, status=400)

        # اقرأ الملف على شكل bytes للتحقق من حجمه ونوعه
        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)  # ← لإرجاع المؤشر كي لا يفقد الملف لاحقًا

        # تحقق من الحجم والنوع
        error = validate_file_upload(file_bytes)
        if error:
            return Response({'error': error}, status=400)

        message = Message.objects.create(
            chat=chat,
            sender=user,
            type='file'
        )

        base, ext = os.path.splitext(uploaded_file.name)
        filename = f"{user.id}_{chat.id}_{int(time.time())}_{base}{ext}"
        message.file.save(filename, uploaded_file)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_id}",
            {
                "type": "chat_message",
                "data": MessageSerializer(message).data
            }
        )
        
        return Response(MessageSerializer(message).data, status=201)

class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
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

        # توليد refresh جديد يدويًا:
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
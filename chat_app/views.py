from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
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
# Create your views here.

class getUser(APIView):
    def get(self, request):
        username = request.GET.get("username")
        user_id = request.GET.get("user_id")
        user = None
        
        if username:
            user = get_object_or_404(User, username=username)
        elif user_id:
            user = get_object_or_404(User, id=user_id)
        else:
            user = get_object_or_404(User, id=request.user.id)
            
        user = UserSerializer(user)
        return Response({
            "user": user.data
        }, status=status.HTTP_200_OK)

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(user1=user) | Chat.objects.filter(user2=user)

    def create(self, request, *args, **kwargs):
        request.data["user1"] = request.user.id
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            chat = serializer.save()

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'chat_updates',
                {
                    'type': 'chat_created',
                    'chat': ChatSerializer(chat).data,
                }
            )

            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs.get('chat_id')
        chat = get_object_or_404(Chat, id=chat_id)
        user = self.request.user
        if user != chat.user1 and user != chat.user2:
            return Message.objects.none()
        return Message.objects.filter(chat=chat)

class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
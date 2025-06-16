"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from .views import *
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')

urlpatterns: list = [
    *router.urls,
    
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    
    path('getUser/', getUser.as_view(), name='getUser'),
    path('logout/', logout.as_view(), name='token_refresh'),
    
    path('chat/<int:chat_id>/messages/', MessageAPIView.as_view(), name='chat-messages'),
    path('messages/<int:chat_id>/upload-audio/', UploadAudioAPIView.as_view(), name='upload-audio'),
    path('messages/<int:chat_id>/upload-file/', UploadFileAPIView.as_view(), name='upload-file'),
    
    path('messages/<int:message_id>/update/', UpdateMessageAPIView.as_view(), name='update-message'),
    path('messages/<int:message_id>/delete/', DeleteMessageAPIView.as_view(), name='delete-message'),
    
    path('markisread/<int:chat_id>/', ChatNotificationsView.as_view(), name='chat-notifications'),
    
    # path('getUsers/', getUsers.as_view(), name='getUsers'),
]

arr: list = 'ziad'
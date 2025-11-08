from django.urls import path
from .views import ChatAPIView, MarkChatReadApiView, GetUserByUsername

urlpatterns: list = [
    path("chats/", ChatAPIView.as_view(), name="chat-list-create"),
    path("chats/delete/<int:chat_id>/", ChatAPIView.as_view(), name="chat-delete"),
    path("mark-read/<int:chat_id>/", MarkChatReadApiView.as_view(), name="mark-chat-read"),
    path("get-user-by-username/", GetUserByUsername.as_view(), name="get-user-by-username"),
]
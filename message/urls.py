from django.urls import path
from .views import MessageAPIView, DeleteMessageAPIView

urlpatterns: list = [
    path("<int:chat_id>/messages/", MessageAPIView.as_view(), name="messages-list"),
    path("delete/<int:message_id>/", DeleteMessageAPIView.as_view(), name="delete-message"),
]
from django.urls import path
from .views import TextMessageAPIView, UpdateTextMessageApiView

urlpatterns: list = [
    path("<int:chat_id>/send-text-message/", TextMessageAPIView.as_view(), name="text-message"),
    path("<int:text_message_id>/update-text-message/", UpdateTextMessageApiView.as_view(), name="update-text-message"),
]
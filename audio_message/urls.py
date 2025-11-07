from django.urls import path
from .views import UploadAudioAPIView

urlpatterns: list = [
    path("<int:chat_id>/uplode-audio/", UploadAudioAPIView.as_view(), name="uplode-audio"),
]
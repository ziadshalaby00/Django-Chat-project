from django.urls import path
from .views import UploadFileAPIView

urlpatterns: list = [
    path("<int:chat_id>/uplode-file/", UploadFileAPIView.as_view(), name="uplode-file"),
]
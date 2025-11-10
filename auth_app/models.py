from django.db import models
import uuid
import os

# Create your models here.
from django.contrib.auth.models import AbstractUser

def user_image_upload_path(instance, filename):
    ext = filename.split('.')[-1] or "jpg"
    unique_name = f"{uuid.uuid4()}.{ext}"
    return os.path.join("users-image", unique_name)

class User(AbstractUser):
    fullname = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    user_image = models.ImageField(upload_to=user_image_upload_path, null=True, blank=True)

    def __str__(self):
        return self.username

from django.contrib.auth.signals import user_logged_in
from django.utils import timezone

def update_last_login_handler(sender, user, request, **kwargs):
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

user_logged_in.connect(update_last_login_handler)

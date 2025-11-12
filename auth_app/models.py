from django.db import models
import uuid
import os

# Create your models here.
from django.contrib.auth.models import AbstractUser

def user_image_upload_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else "jpg"
    unique_name = f"{uuid.uuid4()}.{ext}"
    return os.path.join("users-image", unique_name)

class User(AbstractUser):
    fullname = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    user_image = models.ImageField(upload_to=user_image_upload_path, null=True, blank=True)
    bio = models.CharField(max_length=450, default='Good talks make good days.')

    def __str__(self):
        return self.username

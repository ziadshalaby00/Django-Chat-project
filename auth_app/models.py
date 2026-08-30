from django.contrib.auth.models import UserManager
from django.core.validators import FileExtensionValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.db import models
import uuid
import os

# Create your models here.
from django.contrib.auth.models import AbstractUser

def validate_image_size(image):
    max_size = 5 * 1024 * 1024  # 5 MB

    if image.size > max_size:
        raise ValidationError("Image size must not exceed 5 MB.")


def user_image_upload_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else "jpg"
    unique_name = f"{uuid.uuid4()}.{ext}"
    return os.path.join("users-image", unique_name)

class ActiveUserManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(
            is_active=True,
            is_deleted=False
        )

class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z0-9][A-Za-z0-9_.-]+[A-Za-z0-9]$',
                message="Username may contain only letters, numbers, underscores, dots, and hyphens."
            )
        ]
    )
    fullname = models.CharField(max_length=150)
    
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    pending_email = models.EmailField(
        null=True,
        blank=True,
        unique=True,
    )
    
    user_image = models.ImageField(
        upload_to=user_image_upload_path, 
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "webp"]
            ),
            validate_image_size,
        ],
        null=True, 
        blank=True
    )
    bio = models.CharField(max_length=450, default='Good talks make good days.', null=True, blank=True)
    
    is_deleted = models.BooleanField(default=False)

    # 👇 managers
    objects = ActiveUserManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.username

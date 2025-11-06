from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    fullname = models.CharField(max_length=150)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username
    


from django.contrib.auth.signals import user_logged_in
from django.utils import timezone

def update_last_login_handler(sender, user, request, **kwargs):
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

user_logged_in.connect(update_last_login_handler)

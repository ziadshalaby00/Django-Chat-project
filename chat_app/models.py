from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError

# Create your models here.
# chat/models.py

class Chat(models.Model):
    user1 = models.ForeignKey(User, related_name='chat_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='chat_user2', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user1', 'user2'],
                name='unique_chat_users_direct'
            )
        ]

    def clean(self):
        if Chat.objects.filter(user1=self.user2, user2=self.user1).exists():
            raise ValidationError('unique_chat_users_direct')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f'{self.id} Chat between {self.user1} and {self.user2}'

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender} sent: {self.content[:30]}'
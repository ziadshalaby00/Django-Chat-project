from django.db import models
from chat.models import Chat
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your models here.

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    type = models.CharField(max_length=25, choices=[
        ('text', 'Text'), 
        ('audio', 'Audio'),
        ('file', 'File')
    ], default='text')
    timestamp = models.DateTimeField(auto_now_add=True)
    isRead = models.BooleanField(default=False)
    reply_to = models.ForeignKey(
        'self', 
        null=True, blank=True, 
        on_delete=models.SET_NULL, 
        related_name='replies'
    )

    def __str__(self):
        return f'{self.sender} sent: {self.type} --- {self.chat}'
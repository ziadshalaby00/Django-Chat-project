from django.db import models
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
# chat/models.py

class Chat(models.Model):
    user1 = models.ForeignKey(User, related_name='chat_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='chat_user2', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user1', 'user2')  # منع تكرار نفس الثنائي

    def __str__(self):
        return f'Chat between {self.user1} and {self.user2}'

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender} sent: {self.content[:30]}'
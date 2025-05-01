from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os
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
    type = models.CharField(max_length=25, choices=[
        ('message', 'message'), 
        ('audio', 'audio'),
        ('file', 'file')
    ], default='message')
    
    content = models.TextField(blank=True, null=True)
    audio_file = models.FileField(upload_to='audio', null=True, blank=True)
    file = models.FileField(upload_to='file', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender} sent: {self.type} --- {self.chat}'
    
@receiver(post_delete, sender=Message)
def delete_attached_files(sender, instance, **kwargs):
    # حذف الملف الصوتي إن وجد
    if instance.audio_file and instance.audio_file.path and os.path.isfile(instance.audio_file.path):
        os.remove(instance.audio_file.path)

    # حذف الملف العام إن وجد
    if instance.file and instance.file.path and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)
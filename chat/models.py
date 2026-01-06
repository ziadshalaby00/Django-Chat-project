from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model

User = get_user_model()

class Chat(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        users = self.participants.select_related('user')[:2]
        usernames = ', '.join(p.user.username for p in users)
        return f"Chat #{self.id} ({usernames})"

class ChatParticipant(models.Model):
    chat = models.ForeignKey(Chat, related_name='participants', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_chat = models.BooleanField(default=False)

    class Meta:
        unique_together = ('chat', 'user')

    def __str__(self):
        status = "deleted" if self.deleted_chat else "active"
        return f"Chat #{self.chat.id} - User: {self.user} ({status})"

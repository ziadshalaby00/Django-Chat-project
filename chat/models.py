from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model

User = get_user_model()

class Chat(models.Model):
    user1 = models.ForeignKey(User, related_name='chat_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='chat_user2', on_delete=models.CASCADE)
    
    user1_deleted_chat = models.BooleanField(default=False)
    user2_deleted_chat = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user1', 'user2'],
                name='unique_chat_users_direct'
            )
        ]

    def clean(self):
        if self.user1.pk > self.user2.pk:
            self.user1, self.user2 = self.user2, self.user1

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'chat_id: {self.id} => Chat between {self.user1} and {self.user2}'

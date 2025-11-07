from django.db import models
from message.models import Message

class TextMessage(models.Model):
    message = models.OneToOneField(
        Message,
        on_delete=models.CASCADE,
        related_name='text_message'
    )
    content = models.TextField(null=False)

    def __str__(self):
        return f'{self.message} --- {self.message.id}'

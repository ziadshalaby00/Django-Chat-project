from django.db import models
from message.models import Message


class AudioMessage(models.Model):
    message = models.OneToOneField(
        Message,
        on_delete=models.CASCADE,
        related_name='audio_message'
    )
    audio_file = models.FileField(upload_to='uploads/chat_audio/', null=True, blank=True)
    audio_duration = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f'Audio Message for Message {self.message_id}'

from django.db import models
from message.models import Message


class FileMessage(models.Model):
    message = models.OneToOneField(
        Message,
        on_delete=models.CASCADE,
        related_name='file_message'
    )

    file = models.FileField(
        upload_to='uploads/chat_files/',
        null=False,
        blank=False
    )

    file_name = models.CharField(max_length=255, null=True, blank=True)

    file_size = models.PositiveIntegerField(null=False)
    file_type = models.CharField(max_length=255, null=False)

    def __str__(self):
        return f"FileMessage #{self.id} for Message #{self.message.id}"

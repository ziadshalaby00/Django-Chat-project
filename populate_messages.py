
import os
import django

# Replace 'myproject.settings' with your Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import os
import random
import string
from django.core.files import File
from chat.models import Chat
from file_message.models import FileMessage
from message.models import Message
from text_message.models import TextMessage
from audio_message.models import AudioMessage


# Settings
chat_id = 31
chat = Chat.objects.get(id=chat_id)

# Get all participants in the chat
participants = list(chat.participants.all())
users = [p.user for p in participants]  # Two users

total_messages = 150

# File paths
import os
image_path = os.getenv('POPULATE_IMAGE_PATH')
audio_path = os.getenv('POPULATE_AUDIO_PATH')

# Function to generate random text
def random_text(length=20):
    letters = string.ascii_letters + string.digits + " "
    return ''.join(random.choice(letters) for _ in range(length))

msg_text_number = 1

for i in range(1, total_messages + 1):
    # Choose a random sender
    sender = random.choice(users)
    
    # Determine message type
    if i % 30 == 0:
        # Every 30 messages: 5 images + 5 audio messages
        for j in range(5):
            # Image message
            msg = Message.objects.create(chat=chat, sender=sender, type='file')
            with open(image_path, 'rb') as f:
                FileMessage.objects.create(
                    message=msg,
                    file=File(f, name=os.path.basename(image_path)),
                    file_name=os.path.basename(image_path),
                    file_size=os.path.getsize(image_path),
                    file_type='image/jpeg'
                )
        for j in range(5):
            # Audio message
            msg = Message.objects.create(chat=chat, sender=sender, type='audio')
            with open(audio_path, 'rb') as f:
                AudioMessage.objects.create(
                    message=msg,
                    audio_file=File(f, name=os.path.basename(audio_path)),
                    audio_duration=10.0  # default duration
                )
    else:
        # Text message
        msg = Message.objects.create(chat=chat, sender=sender, type='text')
        content = random_text(length=random.randint(15, 50)) + f' {msg_text_number}'  # random text length between 15-50
        TextMessage.objects.create(message=msg, content=content)
        msg_text_number += 1

print("All messages have been created successfully!")
from django.utils import timezone
from datetime import datetime
from .models import ChatParticipant

def created_after(participant: ChatParticipant) -> datetime :
    return participant.deleted_at or timezone.make_aware(datetime.min)
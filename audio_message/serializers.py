from rest_framework import serializers
from .models import AudioMessage

class AudioMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioMessage
        fields = ['audio_file', 'audio_duration']
        read_only_fields = ['audio_duration']
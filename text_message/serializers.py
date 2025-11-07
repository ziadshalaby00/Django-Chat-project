from rest_framework import serializers
from .models import TextMessage

class TextMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextMessage
        fields = ['id', 'content']

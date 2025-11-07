from rest_framework import serializers
from .models import FileMessage

class FileMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileMessage
        fields = ['file', 'file_name', 'file_size', 'file_type']
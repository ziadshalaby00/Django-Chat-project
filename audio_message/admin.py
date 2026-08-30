from django.contrib import admin
from .models import AudioMessage
from unfold.admin import ModelAdmin

@admin.register(AudioMessage)
class AudioMessageAdmin(ModelAdmin):
    pass
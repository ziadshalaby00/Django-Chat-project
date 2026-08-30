from django.contrib import admin
from .models import TextMessage
from unfold.admin import ModelAdmin

@admin.register(TextMessage)
class TextMessageAdmin(ModelAdmin):
    pass
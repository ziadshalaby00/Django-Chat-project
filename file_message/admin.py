from django.contrib import admin
from .models import FileMessage
from unfold.admin import ModelAdmin

@admin.register(FileMessage)
class FileMessageAdmin(ModelAdmin):
    pass
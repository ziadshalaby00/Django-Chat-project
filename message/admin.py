from django.contrib import admin
from .models import Message
# Register your models here.
from unfold.admin import ModelAdmin

@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_filter = ["type", "chat"]
    search_fields = ["id"]
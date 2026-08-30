from django.contrib import admin
from .models import Chat, ChatParticipant
from unfold.admin import ModelAdmin

# Register your models here.
@admin.register(Chat)
class ChatAdmin(ModelAdmin):
    pass

@admin.register(ChatParticipant)
class ChatParticipantAdmin(ModelAdmin):
    pass
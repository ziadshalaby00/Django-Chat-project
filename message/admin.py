from django.contrib import admin
from .models import Message
# Register your models here.

class MessageAdmin(admin.ModelAdmin):
    list_filter = ['type', 'chat']
    search_fields = ['id']

admin.site.register(Message, MessageAdmin)
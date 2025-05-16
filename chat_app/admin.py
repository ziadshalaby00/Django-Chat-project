from django.contrib import admin
from .models import *

# Register your models here.
class MessageAdmin(admin.ModelAdmin):
    list_filter = ['type', 'chat']  # فلترة حسب النوع
    search_fields = ['id']

admin.site.register(Chat)
admin.site.register(Message, MessageAdmin)
admin.site.register(AudioMessage)
admin.site.register(FileMessage)
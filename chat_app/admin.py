from django.contrib import admin
from .models import *

# Register your models here.
class MessageAdmin(admin.ModelAdmin):
    list_filter = ['type']  # فلترة حسب النوع

admin.site.register(Chat)
admin.site.register(Message, MessageAdmin)
from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # نعدل على fieldsets بالكامل بدل + 
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("fullname", "email", "first_name", "last_name", "user_image", "bio")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "fullname", "email", "password1", "password2", "user_image", "bio"),
        }),
    )

    list_display = ["id", "username", "email", "fullname", "is_staff", "is_active"]

admin.site.site_header = "Proton Admin"      # العنوان اللي في الأعلى
admin.site.site_title = "Proton Admin Portal" # العنوان في تبويب المتصفح
admin.site.index_title = "Welcome to Ziad Admin Dashboard"  # النص في الصفحة الرئيسية

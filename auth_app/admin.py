from unfold.admin import ModelAdmin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from .models import User

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

from unfold.forms import (
    UserChangeForm,
    UserCreationForm,
    AdminPasswordChangeForm,
)

@admin.register(User)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    
    fieldsets = (
        (None, {
            "fields": ("username", "password")
        }),
        ("Personal info", {
            "fields": (
                "fullname",
                "email",
                "pending_email",
                "is_email_verified",
                "user_image",
                "bio",
            )
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_deleted",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important dates", {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "fullname",
                "email",
                "password1",
                "password2",
                "user_image",
                "bio",
            ),
        }),
    )

    list_display = (
        "id",
        "username",
        "email",
        "fullname",
        "is_email_verified",
        "is_staff",
        "is_active",
        "is_deleted",
    )
    
    list_display_links = (
        "id",
        "username",
    )

    list_filter = (
        "is_email_verified",
        "is_staff",
        "is_active",
        "is_deleted",
        "is_superuser",
    )

    search_fields = (
        "username",
        "fullname",
        "email",
        "pending_email",
    )

    ordering = ("id",)

    def get_queryset(self, request):
        return User.all_objects.all()



from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group

admin.site.unregister(Group)

@admin.register(Group)
class CustomGroupAdmin(GroupAdmin, ModelAdmin):
    pass



from rest_framework_simplejwt.token_blacklist.admin import (
    OutstandingTokenAdmin,
    BlacklistedTokenAdmin,
)

from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)

admin.site.unregister(OutstandingToken)
admin.site.unregister(BlacklistedToken)


@admin.register(OutstandingToken)
class CustomOutstandingTokenAdmin(OutstandingTokenAdmin, ModelAdmin):
    pass


@admin.register(BlacklistedToken)
class CustomBlacklistedTokenAdmin(BlacklistedTokenAdmin, ModelAdmin):
    pass
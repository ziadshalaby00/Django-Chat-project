from django.conf import settings

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

def set_jwt_cookie(response, key, value, max_age):
    response.set_cookie(
        key=key,
        value=value,
        httponly=settings.HTTPONLY,
        secure=settings.SECURE,
        samesite=settings.SAMESITE,
        max_age=max_age,
        path=settings.COOKIE_PATH
    )
    return response
    
def clear_auth_cookies(response):
    response.delete_cookie("access", path=settings.COOKIE_PATH, samesite=settings.SAMESITE)
    response.delete_cookie("refresh", path=settings.COOKIE_PATH, samesite=settings.SAMESITE)
    return response

from django.utils import timezone
def update_user_login(user):
    if isinstance(user, AnonymousUser):
        return
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
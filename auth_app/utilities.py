from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

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

def specific_send_mail(*, subject, message, link, from_email, recipient_list):
    plain_message = f"{message}\n\nUse this link if the button doesn't work:\n{link}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background: #f5f7fa; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
        
        <h2 style="text-align: center; color: #4A90E2;">🔐 Reset Your Password</h2>

        <p style="font-size: 16px; color: #333;">
            {message}
        </p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{link}" 
            style="background: #4A90E2; color: white; padding: 12px 20px; 
                    text-decoration: none; font-size: 16px; border-radius: 6px;">
            Reset Password
            </a>
        </div>

        <p style="font-size: 14px; color: #777;">
            If the button doesn’t work, copy and paste this link:
        </p>

        <p style="word-break: break-all; color: #555;">
            {link}
        </p>

        </div>
    </body>
    </html>
    """

    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=from_email,
        to=recipient_list
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


from django.utils import timezone
def update_user_login(user):
    if isinstance(user, AnonymousUser):
        return
    user.save(update_fields=["last_login"])


def get_user_from_access_token(token_str):
    try:
        token = UntypedToken(token_str)
        user_id = token.payload.get("user_id")
        if user_id:
            return User.objects.get(id=user_id)
    except (TokenError, User.DoesNotExist, InvalidToken):
        return None
from celery import shared_task
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .send_email import send_email_ui
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_verification_email_task(user_id, email):
    user = User.objects.get(pk=user_id)

    from .views.email import send_verification_email

    send_verification_email(user, email)



@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_password_reset_email_task(user_id):
    user = User.objects.get(pk=user_id)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    reset_url = (
        f"{settings.FRONTEND_URL}"
        f"/reset-password/{uid}/{token}/"
    )

    send_email_ui(
        subject="Reset Your Password",
        heading="Password Reset Request",
        message=(
            f"Hi {user.fullname or user.username},<br><br>"
            "We received a request to reset your password. "
            "Click the button below to choose a new password.<br><br>"
            "If you didn't request a password reset, you can safely ignore this email."
        ),
        button_text="Reset Password",
        link=reset_url,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        button_color="#dc3545",
        icon="🔒",
        footer_message=(
            "For your security, this password reset link will expire after a limited time."
        ),
    )
    


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def download_google_profile_image_task(user_id, picture_url):
    import requests

    from django.core.files.base import ContentFile

    user = User.objects.get(pk=user_id)

    response = requests.get(
        picture_url,
        timeout=10,
    )

    response.raise_for_status()
    
    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        raise ValueError("Invalid image content type")

    user.user_image.save(
        "google-profile.jpg",
        ContentFile(response.content),
        save=True,
    )
    
    
from celery import shared_task
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)

@shared_task
def cleanup_expired_blacklisted_tokens_task():
    now = timezone.now()

    expired_tokens = OutstandingToken.objects.filter(
        expires_at__lt=now,
        blacklistedtoken__isnull=False,
    )

    deleted_count, _ = expired_tokens.delete()

    return deleted_count
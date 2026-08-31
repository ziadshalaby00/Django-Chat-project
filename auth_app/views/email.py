from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from ..send_email import (
    send_email_ui, 
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import AllowAny
from .config import *

class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk)
            + str(timestamp)
            + str(user.pending_email)
            + str(user.is_email_verified)
        )

email_verification_token = EmailVerificationTokenGenerator()

def send_verification_email(user, email):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)

    verification_url = (
        f"{settings.FRONTEND_URL}"
        f"/verify-email/{uid}/{token}/"
    )

    send_email_ui(
        subject="Verify Your Email Address",
        heading="Verify Your Email",
        message=(
            f"Hi {user.fullname or user.username},<br><br>"
            "Thank you for creating an account. "
            "Please verify your email address by clicking the button below. "
            "This helps us keep your account secure."
        ),
        button_text="Verify Email",
        link=verification_url,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        button_color="#28a745",
        icon="📧",
    )
    
from django.db import transaction
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

class EmailVerificationView(APIView): # Verfiy email
    permission_classes = [AllowAny]
    throttle_classes = [MainThrottle]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")

        if not uid or not token:
            return Response(
                {"detail": "UID and token are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response(
                {"detail": "Invalid verification link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not email_verification_token.check_token(user, token):
            return Response(
                {"detail": "Verification link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            if user.pending_email:
                user.email = user.pending_email
                user.pending_email = None
                user.save(update_fields=["email", "pending_email"])
            else:
                if user.is_email_verified:
                    return Response(
                        {"detail": "Email is already verified."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                user.is_email_verified = True
                user.save(update_fields=["is_email_verified"])

        return Response(
            {"detail": "Email verified successfully."},
            status=status.HTTP_200_OK,
        )

from django.db.models import Q
class ResendVerificationEmailView(APIView): # Resend verification email
    permission_classes = [AllowAny]
    throttle_classes = [SecondThrottle]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(
            Q(email=email) | Q(pending_email=email)
        ).first()

        if user is None:
            return Response(
                {"detail": "If the account exists, a verification email has been sent."},
                status=status.HTTP_200_OK,
            )

        from ..tasks import send_verification_email_task
        
        if not user.is_email_verified:
            send_verification_email_task.delay(
                user.id,
                user.email,
            )
            
            return Response(
                {"detail": "If the account exists, a verification email has been sent."},
                status=status.HTTP_200_OK,
            )
        
        if user.pending_email:
            send_verification_email_task.delay(
                user.id,
                user.pending_email,
            )
            
            return Response(
                {"detail": "A verification link has been sent to your email address."},
                status=status.HTTP_200_OK,
            )

        
        return Response(
            {"detail": "There is no email waiting for verification."},
            status=status.HTTP_400_BAD_REQUEST,
        )
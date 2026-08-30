from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import AllowAny
from django.conf import settings

from ..serializers import PasswordResetConfirmSerializer
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes

from .config import *
from django.conf import settings


class SendPasswordResetLinkView(APIView): # Forgot Password
    permission_classes = [AllowAny]
    throttle_classes = [SecondThrottle]
    
    def post(self, request):
        email = request.data.get("email", "").strip()
        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user = User.objects.filter(email=email).first()
        if user:
            from ..tasks import send_password_reset_email_task
            print("BROKER:", settings.CELERY_BROKER_URL)
            send_password_reset_email_task.delay(user.id)
            
        return Response(
            {"message": "If the email exists, a password reset link has been sent."},
            status=status.HTTP_200_OK
        )

class PasswordResetConfirmView(APIView): # Reset Confirm Password
    permission_classes = [AllowAny]
    throttle_classes = [MainThrottle]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)

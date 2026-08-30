from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import AllowAny
from rest_framework.generics import RetrieveAPIView

from ..serializers import UserSerializer, OtherUsersSerializer

from rest_framework.permissions import IsAuthenticated
from ..serializers import UserUpdateSerializer

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from rest_framework.decorators import api_view, permission_classes, throttle_classes
from .config import *
from .email import send_verification_email
    
    
class UserUpdateView(APIView): # Update User
    permission_classes = [IsAuthenticated]
    throttle_classes = [MainThrottle]

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user = UserSerializer(request.user, context={"request": request}).data
        return Response({
            "message": "User updated successfully",
            "user": user
        }, status=status.HTTP_200_OK)

class ChangeEmailView(APIView): # Change Email
    permission_classes = [IsAuthenticated]
    throttle_classes = [MainThrottle]

    def post(self, request):
        new_email = request.data.get("new_email")

        if not new_email:
            return Response(
                {"detail": "New Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_email(new_email)
        except ValidationError:
            return Response(
                {"detail": "Enter a valid email address."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user

        if new_email == user.email:
            return Response(
                {"detail": "This is already your current email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=new_email).exists():
            return Response(
                {"detail": "This email is already registered."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(pending_email=new_email).exclude(pk=user.pk).exists():
            return Response(
                {"detail": "This email is already pending verification."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user.pending_email = new_email
            user.save(update_fields=["pending_email"])
        except IntegrityError:
            return Response(
                {"detail": "This email is already in use or pending verification."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from ..tasks import send_verification_email_task
        send_verification_email_task.delay(
            user.id,
            user.pending_email,
        )

        return Response(
            {"detail": "A verification link has been sent to your new email address."},
            status=status.HTTP_200_OK,
        )

class UserProfileView(RetrieveAPIView): # Me
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [MainThrottle]

    def get_object(self):
        return self.request.user


class OtherUsersProfileView(APIView): # Get Users Profile (Optional If System Needed It)
    permission_classes = [AllowAny]
    throttle_classes = [MainThrottle]
    """
    Return another user's public profile by ID
    """

    def get(self, request, id):
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return  Response({
                "detail": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)

        user_profile = OtherUsersSerializer(user, context={"request": request}).data
        return Response({
            "user_profile": user_profile
        }, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@throttle_classes([MainThrottle])
def delete_user_image(request):
    user = request.user

    if user.user_image:
        user.user_image.delete(save=False)
        user.user_image = None
        user.save(update_fields=["user_image"])

        return Response({
            "message": "User image deleted successfully"
        }, status=status.HTTP_200_OK)

    return Response({
        "message": "User image already deleted or not set"
    }, status=status.HTTP_200_OK)
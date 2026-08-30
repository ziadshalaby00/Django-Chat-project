from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction
from hashlib import sha256

from ..utilities import (
    clear_auth_cookies
)

from rest_framework.permissions import IsAuthenticated
from .config import *


class DeleteUserView(APIView): # Delete account
    permission_classes = [IsAuthenticated]
    throttle_classes = [MainThrottle]

    def post(self, request):
        user = request.user
        password = request.data.get("password")

        if not password:
            return Response({"error": "Password is required to delete account"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"error": "Incorrect password"}, status=status.HTTP_401_UNAUTHORIZED)

        # ========== SOFT DELETE + ANONYMIZE ==========
        with transaction.atomic():
            user.fullname = "Deleted User"
            
            # username hash:
            hashed_id = sha256(str(user.id).encode()).hexdigest()[:16]
            user.username = f"__deleted__{hashed_id}"

            user.email = f"__deleted__{hashed_id}@example.com"
            user.pending_email = None
            user.bio = None
            
            if user.user_image:
                user.user_image.delete(save=False)
            user.user_image = None
            
            user.set_unusable_password() # cannot login again
            
            user.is_deleted = True
            user.is_active = False
            user.is_email_verified = False
            
            user.save()

        # ========== CLEAR COOKIES ==========
        response = Response({"message": "User account deleted successfully"}, status=status.HTTP_200_OK)
        response = clear_auth_cookies(response)

        return response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import AllowAny
from django.conf import settings

import requests
from requests.exceptions import Timeout, RequestException
from rest_framework_simplejwt.tokens import RefreshToken

from ..utilities import (
    set_jwt_cookie,
    update_user_login,
)

from django.core.files.base import ContentFile

from django.utils.text import slugify
from uuid import uuid4

from .config import *

class GoogleLoginView(APIView): # Google Login
    permission_classes = [AllowAny]
    throttle_classes = [MainThrottle]
    
    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"error": "No Google code provided"}, status=400)

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            "client_secret": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
            "redirect_uri": "postmessage",
            "grant_type": "authorization_code",
        }

        try:
            r = requests.post(token_url, data=data, timeout=10)
            r.raise_for_status()
        except Timeout:
            return Response(
                {"error": "Google request timed out"},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except RequestException:
            return Response(
                {"error": "Failed to exchange Google code"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        tokens = r.json()
        id_token_value = tokens.get("id_token")

        if not id_token_value:
            return Response({"error": "No id_token in response"}, status=400)

        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_value, google_requests.Request(), settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
            )
            email = idinfo.get("email")
            fullname = idinfo.get("name")
            
            base = slugify(email.split("@")[0]) or "user"
            username = f"{base}_{uuid4().hex[:8]}"
            
            picture_url = idinfo.get("picture")

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": username, 
                    "fullname": fullname,
                    "is_email_verified": True,
                },
            )
            
            if not created and not user.is_email_verified:
                user.is_email_verified = True
                user.save(update_fields=["is_email_verified"])
                        
            if created and picture_url:
                from ..tasks import download_google_profile_image_task
                download_google_profile_image_task.delay(
                    user.id,
                    picture_url,
                )
                
            update_user_login(user)
            
            refresh = RefreshToken.for_user(user)
            response = Response(
                {"message": "Successfully logged in with Google"},
                status=status.HTTP_200_OK,
            )
            
            response = set_jwt_cookie(response, "access", str(refresh.access_token), settings.ACCESS_MAX_AGE)
            response = set_jwt_cookie(response, "refresh", str(refresh), settings.REFRESH_MAX_AGE)

            return response
        
        except Exception:
            return Response({"error": "Invalid Google token"}, status=400)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import AllowAny
from django.conf import settings

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from rest_framework_simplejwt.views import TokenVerifyView
from rest_framework_simplejwt.serializers import TokenVerifySerializer
from rest_framework_simplejwt.exceptions import TokenError

from auth_app.serializers import UserRegisterSerializer
from rest_framework import serializers

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from ..utilities import (
    clear_auth_cookies,
    set_jwt_cookie,
    update_user_login,
)

from .config import *
from .email import send_verification_email

class RegisterView(APIView): # Register
    permission_classes = [AllowAny]
    throttle_classes = [MainThrottle]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            
            from ..tasks import send_verification_email_task
            send_verification_email_task.delay(
                user.id,
                user.email,
            )

            return Response(
                {
                    "message": (
                        "Registration successful. "
                        "A verification link has been sent to your email address."
                    )
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.is_email_verified:
            raise serializers.ValidationError(
                {"detail": "Please verify your email before logging in."}
            )

        return data

class CookieTokenObtainPairView(TokenObtainPairView): # Login
    permission_classes = [AllowAny]
    throttle_classes = [SecondThrottle]
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        access = serializer.validated_data["access"]
        refresh = serializer.validated_data["refresh"]

        update_user_login(serializer.user)

        res = Response({"message": "Logged in successfully"})

        set_jwt_cookie(res, "access", access, settings.ACCESS_MAX_AGE)
        set_jwt_cookie(res, "refresh", refresh, settings.REFRESH_MAX_AGE)

        return res
    
class CookieTokenRefreshView(TokenRefreshView): # Refresh
    permission_classes = [AllowAny]
    throttle_classes = [MainThrottle]
    serializer_class = TokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh")

        if refresh_token is None:
            return Response({"error": "No refresh token in cookie"}, status=400)

        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response(
                {"detail": "Refresh token is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access = serializer.validated_data["access"]
        refresh = serializer.validated_data["refresh"]

        res = Response({"message": "Access and refresh tokens refreshed"})

        res = set_jwt_cookie(res, "access", access, settings.ACCESS_MAX_AGE)
        res = set_jwt_cookie(res, "refresh", refresh, settings.REFRESH_MAX_AGE)
        
        return res


class CookieTokenVerifyView(TokenVerifyView): # Verfivy Token
    permission_classes = [AllowAny]
    throttle_classes = [MainThrottle]
    serializer_class = TokenVerifySerializer

    def post(self, request, *args, **kwargs):
        access_token = request.COOKIES.get("access")

        if access_token is None:
            return Response(
                {"status": "no_token", "message": "No access token in cookie"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data={"token": access_token})

        try:
            serializer.is_valid(raise_exception=True)
            return Response(
                {"message": "Access token is valid"},
                status=status.HTTP_200_OK,
            )
        except TokenError as e:
            return Response(
                {"message": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            
class LogoutView(APIView): # Logut
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [MainThrottle]

    def post(self, request):
        refresh = request.COOKIES.get("refresh")

        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except TokenError:
                pass

        response = Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_200_OK
        )

        clear_auth_cookies(response)

        return response
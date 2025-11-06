from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import AllowAny
from django.conf import settings
from rest_framework.generics import RetrieveAPIView

from .serializers import UserRegisterSerializer, UserSerializer

import requests
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from rest_framework_simplejwt.views import TokenVerifyView
from rest_framework_simplejwt.serializers import TokenVerifySerializer
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .serializers import SendPasswordResetLinkSerializer, PasswordResetConfirmSerializer
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from .utilities import clear_auth_cookies, set_jwt_cookie, specific_send_mail

from rest_framework.permissions import IsAuthenticated
from .serializers import UserUpdateSerializer

# views.py
from rest_framework.decorators import api_view
from django.views.decorators.csrf import ensure_csrf_cookie

from django.contrib.auth import get_user_model
User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User registered successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CookieTokenObtainPairView(TokenObtainPairView): # Login
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)  # استدعاء الكلاس الأصلي
        data = response.data

        access = data.get("access")
        refresh = data.get("refresh")

        res = Response({"message": "Loggedin successfully"})

        if access:
            res = set_jwt_cookie(res, "access", access, settings.ACCESS_MAX_AGE)
            
        if refresh:
            res = set_jwt_cookie(res, "refresh", refresh, settings.REFRESH_MAX_AGE)

        return res
    
class CookieTokenRefreshView(TokenRefreshView): # Refresh
    serializer_class = TokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh")

        if refresh_token is None:
            return Response({"error": "No refresh token in cookie"}, status=400)

        serializer = self.get_serializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)

        access = serializer.validated_data["access"]
        refresh = serializer.validated_data["refresh"]

        res = Response({"message": "Access and refresh tokens refreshed"})

        res = set_jwt_cookie(res, "access", access, settings.ACCESS_MAX_AGE)
        res = set_jwt_cookie(res, "refresh", refresh, settings.REFRESH_MAX_AGE)
        
        return res

class CookieTokenVerifyView(TokenVerifyView): # Verfivy Token
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
        except InvalidToken as e:
            return Response(
                {"message": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

class GoogleLoginView(APIView): # Google Login
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

        r = requests.post(token_url, data=data)
        if r.status_code != 200:
            return Response({"error": "Failed to exchange code"}, status=400)

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
            username = email.split("@")[0]

            user, created = User.objects.get_or_create(
                email=email,
                defaults={"username": username, "fullname": fullname},
            )
                
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

class SendPasswordResetLinkView(APIView): # Forgot Password
    def post(self, request):
        serializer = SendPasswordResetLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

        specific_send_mail(
            subject="Password Reset Request",
            message=f"Click the link to reset your password",
            link=reset_url,
            from_email=None,
            recipient_list=[email],
        )

        return Response({"message": "Password reset link sent to your email."}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView): # Reset Password
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)

class UserUpdateView(APIView): # Update User
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "User updated successfully"}, status=status.HTTP_200_OK)

class LogoutView(APIView): # Logut
    def post(self, request):
        response = Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        
        response = clear_auth_cookies(response)
        return response

class DeleteUserView(APIView): # Delete User
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        password = request.data.get("password")

        if not password:
            return Response({"error": "Password is required to delete account"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"error": "Incorrect password"}, status=status.HTTP_401_UNAUTHORIZED)

        user.delete()

        response = Response({"message": "User account deleted successfully"}, status=status.HTTP_200_OK)
        response = clear_auth_cookies(response)

        return response

class UserProfileView(RetrieveAPIView): # Me
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

@api_view(["GET"])
@ensure_csrf_cookie
def get_csrf(request): # Csrf Token
    """
    Call this once on app load to ensure csrftoken cookie is set.
    """
    return Response({"detail": "CSRF cookie set"})
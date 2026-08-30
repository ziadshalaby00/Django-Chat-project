from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.permissions import AllowAny

@api_view(["GET"])
@ensure_csrf_cookie
@authentication_classes([])
@permission_classes([AllowAny])
def get_csrf(request): # Csrf Token
    """
    Call this once on app load to ensure csrftoken cookie is set.
    """
    return Response({"detail": "CSRF cookie set"})
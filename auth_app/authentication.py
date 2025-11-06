from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get("access")
        if not access_token:
            return None

        request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        return super().authenticate(request)

'''_core/settings.py_

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        ...,
        "auth_app.authentication.CookieJWTAuthentication",
        ...
    )
}

'''

# ======================================================================
# ======================================================================

# auth_app/authentication.py
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.exceptions import PermissionDenied
from django.conf import settings

class CSRFMiddlewareWithJWT:
    """
    Middleware to enforce CSRF validation for POST/PUT/PATCH/DELETE requests
    when using JWT in cookies.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_patterns = getattr(settings, "CSRF_EXEMPT_URL_PATTERNS", [])

    def process_view(self, request, view_func, view_args, view_kwargs):
        path = request.path
        
        for pattern in self.exempt_patterns:
            if pattern.fullmatch(path):
                return None
        
        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            reason = CsrfViewMiddleware(lambda r: None).process_view(
                request,
                callback=None,
                callback_args=(),
                callback_kwargs={}
            )
            if reason:
                raise PermissionDenied("CSRF Verification Failed")

        return None

    def __call__(self, request):
        return self.get_response(request)

'''_core/settings.py_

MIDDLEWARE = [
    ...,
    "auth_app.authentication.CSRFMiddlewareWithJWT",
    ...
]

'''
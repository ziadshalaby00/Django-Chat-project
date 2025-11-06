from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

class CookieJWTAuthWebSocket(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])

        # =============================
        # 1) استخراج Cookies
        # =============================
        cookie_header = headers.get(b'cookie', b'').decode()
        cookies = {}
        for part in cookie_header.split(";"):
            if "=" in part:
                name, value = part.strip().split("=", 1)
                cookies[name] = value

        access_token = cookies.get("access")
        csrf_cookie = cookies.get("csrftoken")

        # =============================
        # 2) استخراج token من query
        # =============================
        query_string = scope.get("query_string", b"").decode()
        csrf_query = None
        if "X-CSRFToken=" in query_string:
            csrf_query = query_string.split("X-CSRFToken=")[-1].split("&")[0]

        # =============================
        # 3) تحقق من CSRF
        # =============================
        print(csrf_cookie)
        print(csrf_query)
        if not self.check_csrf(csrf_cookie, csrf_query):
            scope["user"] = AnonymousUser()
            return await super().__call__(scope, receive, send)


        # =============================
        # 4) تحقق من JWT
        # =============================
        scope["user"] = await self.get_user(access_token)

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token):
        if not token:
            return AnonymousUser()
        try:
            at = AccessToken(token)
            return User.objects.get(id=at["user_id"])
        except:
            return AnonymousUser()

    # =======================================
    # دالة التحقق من CSRF
    # =======================================
    def check_csrf(self, csrf_cookie, csrf_query):
        return csrf_cookie == csrf_query

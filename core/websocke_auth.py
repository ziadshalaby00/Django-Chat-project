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

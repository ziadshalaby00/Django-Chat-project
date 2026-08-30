from rest_framework.throttling import SimpleRateThrottle

from django.contrib.auth import get_user_model

User = get_user_model()


class MainThrottle(SimpleRateThrottle):
    scope = "main"
    
    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"throttle:{self.scope}:{view.__class__.__name__}:{ident}"

class SecondThrottle(SimpleRateThrottle):
    scope = "second"
        
    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"throttle:{self.scope}:{view.__class__.__name__}:{ident}"

from rest_framework.routers import DefaultRouter
from .views import ChatViewSet

router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')

urlpatterns: list = [
    *router.urls,
]
from django.urls import path
from .views import (
    RegisterView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    CookieTokenVerifyView,
    GoogleLoginView,
    PasswordResetConfirmView,
    SendPasswordResetLinkView,
    UserUpdateView,
    LogoutView,
    DeleteUserView,
    UserProfileView,
    get_csrf,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CookieTokenObtainPairView.as_view(), name="token_obtain_pair"),
    
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", CookieTokenVerifyView.as_view(), name="token_verify"),
    
    path("google-login/", GoogleLoginView.as_view(), name="google_login"),
    
    path("password-reset-link/", SendPasswordResetLinkView.as_view(), name="password_reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    
    path("update-profile/", UserUpdateView.as_view(), name="update_profile"),
    
    path("logout/", LogoutView.as_view(), name="logout"),
    
    path("get_csrf/", get_csrf, name="get_csrf"),

    path("me/", UserProfileView.as_view(), name="user-profile"),
    path("delete-user/", DeleteUserView.as_view(), name="delete_user"),
]


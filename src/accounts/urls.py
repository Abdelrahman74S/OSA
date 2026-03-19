from django.urls import path
from .views import (
    RegisterViews, LoginViews, LogoutView,
    ListUserProfileView, UserProfileView,
    RequestPasswordReset, ResetPassword, ChangePasswordView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # --- Authentication ---
    path('auth/register/', RegisterViews.as_view(), name='register'),
    path('auth/login/', LoginViews.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # --- Profiles ---
    # List view (Staff sees all, Users see self)
    path('users/', ListUserProfileView.as_view(), name='user-list'),
    
    # Detail view (Uses UUID)
    path('users/<uuid:id>/', UserProfileView.as_view(), name='user-detail'),

    # --- Password Management ---
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/password-reset-request/', RequestPasswordReset.as_view(), name='password-reset-request'),
    path('auth/password-reset-confirm/<str:uidb64>/<str:token>/', ResetPassword.as_view(), name='password-reset-confirm'),
]
"""URLs pour les utilisateurs et l'authentification"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, TokenRefreshCustomView,
    LogoutView, UserViewSet
)

app_name = 'users'

# Router pour les viewsets
router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    # Authentification
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('refresh/', TokenRefreshCustomView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view({'post': 'logout'}), name='logout'),
    
    # Utilisateurs
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterViewSet, LoginViewSet, BlogViewSet, UserViewSet


router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='api-register')
router.register(r'login', LoginViewSet, basename='api-login')
router.register(r'blogs', BlogViewSet, basename='blog')
router.register(r'users', UserViewSet, basename='user')  # Register the User API


urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]

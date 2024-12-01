from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterViewSet, LoginViewSet, BlogViewSet
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='api-register')
router.register(r'login', LoginViewSet, basename='api-login')
router.register(r'blogs', BlogViewSet, basename='blog')


urlpatterns = [
    path('', include(router.urls)),
]

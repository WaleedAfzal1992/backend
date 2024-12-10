from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer, LoginSerializer
from django.contrib.auth.models import User
from .models import Blog, BlogPermission
from .serializers import BlogSerializer, BlogPermissionSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q
from .serializers import UserSerializer
from rest_framework.permissions import BasePermission
import logging
logger = logging.getLogger(__name__)


# API ViewSets
class RegisterViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': serializer.data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)


class LoginViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)


class IsEditorOrAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        # Check if user is the author or has permissions
        return obj.author == user or BlogPermission.objects.filter(blog=obj, user=user).exists()


class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    permission_classes = [IsAuthenticated, IsEditorOrAuthor]

    def get_queryset(self):
        user = self.request.user
        # Fetch blogs where the user is the author or has permission
        return Blog.objects.filter(Q(author=user) | Q(blogpermission__user=user)).distinct()

    def perform_create(self, serializer):
        blog = serializer.save()  # Save the blog object first
        user = self.request.user  # Get the current logged-in user

        # This will either get the existing BlogPermission or create a new one if it doesn't exist
        BlogPermission.objects.get_or_create(
            blog=blog,
            user=user,
            defaults={'permission_type': 'your_permission_type'}  # Set the default permission type
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def grant_access(self, request, pk=None):
        blog = self.get_object()
        user_id = request.data.get('user_id')
        permission_type = request.data.get('permission_type')

        if not user_id or not permission_type:
            return Response({"detail": "Missing data."}, status=400)

        # Create or update the BlogPermission record
        user = self.get_user_by_id(user_id)
        if user:
            # Validate and create BlogPermission
            permission = BlogPermission.objects.update_or_create(
                blog=blog,
                user=user,
                defaults={'permission_type': permission_type}
            )
            return Response({'detail': f'Permission "{permission_type}" granted to {user.username}.'}, status=200)
        return Response({"detail": "User not found."}, status=404)

    def get_user_by_id(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def permissions(self, request, pk=None):
        blog = self.get_object()
        user = request.user

        permission = BlogPermission.objects.filter(blog=blog, user=user).first()
        if permission:
            return Response({
                'can_update': permission.permission_type == 'Full Access',
                'can_delete': permission.permission_type == 'Full Access',
            })
        else:
            return Response({'can_update': False, 'can_delete': False})

    def retrieve(self, request, *args, **kwargs):
        # Fetch blog object
        blog = self.get_object()
        # Check permissions for the current user
        permission = BlogPermission.objects.filter(blog=blog, user=request.user).first()

        # Add permission data to the response
        blog_data = BlogSerializer(blog).data
        if permission:
            blog_data['can_update'] = permission.permission_type == 'Full Access'
            blog_data['can_delete'] = permission.permission_type == 'Full Access'
        else:
            blog_data['can_update'] = False
            blog_data['can_delete'] = False

        return Response(blog_data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Blog, BlogPermission


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    token = serializers.CharField(read_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                data['user'] = user
            else:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
        else:
            raise serializers.ValidationError('Must include "username" and "password".')

        return data


class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ['id', 'title', 'content', 'created_at', 'author']
        read_only_fields = ['id', 'created_at', 'author']

    def create(self, validated_data):
        # Get the currently authenticated user from the request context
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class BlogPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPermission
        fields = ['blog', 'user', 'permission_type']
        read_only_fields = ['blog']

    def create(self, validated_data):
        # Ensure the user has permission to grant permissions
        request_user = self.context['request'].user
        blog = validated_data.get('blog')

        if not BlogPermission.objects.filter(blog=blog, user=request_user, permission_type='Full Access').exists():
            raise serializers.ValidationError("You do not have permission to grant access to this blog.")

        return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']  # Add more fields as needed

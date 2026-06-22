from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.core.cache import cache

from .serializers import RegisterSerializer, UserSerializer
from .permissions import IsTeacherOrAdmin, IsOwnerOrAdmin
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

import requests
from urllib.parse import urlencode
from django.conf import settings

from .tasks import send_welcome_email

GOOGLE_AUTH_URL     = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL    = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL     = "https://www.googleapis.com/oauth2/v3/userinfo"


User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        send_welcome_email.delay(user.email, user.full_name)

        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_201_CREATED
        )

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsTeacherOrAdmin]

    def list(self, request, *args, **kwargs):
        cache_key = "users:all"

        data = cache.get(cache_key)

        if not data:
            users = User.objects.all()
            data = UserSerializer(users,many=True).data

            cache.set(
                cache_key,
                data,
                timeout=60 * 1
            )

        return Response(data)

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_update(self, serializer):
        serializer.save()
        cache.delete("users:all")

    def perform_destroy(self, instance):
        cache.delete("users:all")
        instance.delete()

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {"detail": "refresh токен обязателен."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Токен недействителен или уже использован."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response({"detail": "Выход выполнен."},
                        status=status.HTTP_200_OK)

class GoogleOAuthRedirectView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        params = urlencode({ #https://accounts.google.com/0/oauth2/v2/auth
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
        })
        return Response({"url": f"{GOOGLE_AUTH_URL}?{params}"})


class GoogleOAuthCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        code = request.query_params.get("code") # ?code=abc123

        if not code:
            return Response(
                {"detail": "code не передан."},
                status=status.HTTP_400_BAD_REQUEST
            )

        token_response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
                "grant_type": "authorization_code",
            }
        )

        if token_response.status_code != 200:
            return Response(
                {
                    "google_status": token_response.status_code,
                    "google_response": token_response.text,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        google_access_token = token_response.json().get("access_token")

        user_info = requests.get(
            GOOGLE_USER_URL,
            headers={
                "Authorization": f"Bearer {google_access_token}"
            }
        ).json()

        email = user_info.get("email")
        full_name = user_info.get("name", "")
        avatar_url = user_info.get("picture", "")

        if not email:
            return Response(
                {"detail": "Google не вернул email."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name": full_name,
                "role": "student",
            }
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            "created": created,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        })
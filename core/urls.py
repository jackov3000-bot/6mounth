from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.serializers import CustomTokenObtainPairView

urlpatterns = [
    path("admin/",                    admin.site.urls),
    path("api/token/",                CustomTokenObtainPairView.as_view()),
    path("api/token/refresh/",        TokenRefreshView.as_view()),
    path("api/accounts/",             include("accounts.urls")),
    path('api/courses/',              include('courses.urls')),
]

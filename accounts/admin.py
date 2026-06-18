from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model         = CustomUser
    list_display  = ["email", "full_name", "role", "is_staff", "created_at"]
    ordering      = ["email"]
    search_fields = ["email", "full_name"]

    fieldsets = (
        (None,           {"fields": ("email", "password")}),
        ("Личные данные",{"fields": ("full_name", "phone", "role", "avatar")}),
        ("Права",        {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields":  ("email", "full_name", "role", "password1", "password2"),
        }),
    )

from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsTeacher(BasePermission):
    message = "Доступ только для преподавателей."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == "teacher"
        )

class IsStudent(BasePermission):
    message = "Доступ только для студентов."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == "student"
        )

class IsAdminRole(BasePermission):
    message = "Доступ только для администраторов."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == "admin"
        )

class IsTeacherOrAdmin(BasePermission):
    message = "Доступ только для преподавателей и администраторов."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ["teacher", "admin"]
        )

class IsOwnerOrAdmin(BasePermission):
    message = "Вы не являетесь владельцем этого объекта."

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        return obj == request.user

class ReadOnlyOrTeacher(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role == "teacher"
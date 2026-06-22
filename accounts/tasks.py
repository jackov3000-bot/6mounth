from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_email, full_name):
    try:
        send_mail(
            subject="Добро пожаловать!",
            message=f"Привет, {full_name}! Регистрация завершена. Камера зафиксировала твое подключение. Пожалуйста, не оборачивайся, пока идет синхронизация данных.Ухахвхахвхахвхахха.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@shared_task
def cleanup_expired_tasks():
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
    from django.utils import timezone
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=7)
    deleted, _ =BlacklistedToken.objects.filter(
        token__created_at__lt=cutoff
    ).delete()
    return f"Удалено {deleted} токенов"
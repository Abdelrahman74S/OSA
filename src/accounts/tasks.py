from celery import shared_task
from django.conf import settings
from .models import User 
from django.core.mail import send_mail

@shared_task
def send_welcome(user_id):
        try:
            user = User.objects.get(pk=user_id)
            subject = 'Welcome to Our Platform'
            message = f'Hi {user.username}, thank you for registering with us!'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user.email]
            send_mail(subject, message, from_email, recipient_list)
        except User.DoesNotExist:
            pass
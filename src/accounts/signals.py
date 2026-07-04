from .models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .tasks import send_welcome
from django.db import transaction

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: send_welcome.delay(instance.id))
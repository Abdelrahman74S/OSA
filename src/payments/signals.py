from django.core.mail import send_mail
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction

@receiver(post_save, sender=Transaction)
def notify_transaction_status_change(sender, instance, created, **kwargs):
    if created:
        return  

    if instance.status == Transaction.Status.PAID:
        send_mail(
            subject=f"Payment received for '{instance.auction.title}'",
            message=f"Hi {instance.seller.username}, your item '{instance.auction.title}' has been paid. Please ship it now.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[instance.seller.email],
            fail_silently=True
        )

    elif instance.status == Transaction.Status.SHIPPED:
        send_mail(
            subject=f"Your item '{instance.auction.title}' is on the way",
            message=f"Hi {instance.buyer.username}, your item '{instance.auction.title}' has been shipped! Tracking number: {instance.tracking_number}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[instance.buyer.email],
            fail_silently=True
        )
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Bid
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=Bid)
def notify_on_new_bid(sender, instance, created, **kwargs):
    if not created:
        return

    auction = instance.auction
    seller_email = auction.seller.email
    bidder_email = instance.bidder.email

    send_mail(
        subject=f"New bid on your item '{auction.title}'",
        message=f"Hi {auction.seller.username}, a new bid of {instance.amount} has been placed on your item '{auction.title}'.",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[seller_email],
        fail_silently=True
    )

    previous_bid = (
        Bid.objects.filter(auction=auction, is_valid=True)
        .exclude(id=instance.id)
        .order_by('-amount')
        .first()
    )

    if previous_bid and previous_bid.bidder != instance.bidder:
        send_mail(
            subject=f"Your bid on '{auction.title}' has been outbid",
            message=f"Hi {previous_bid.bidder.username}, your previous bid of {previous_bid.amount} has been outbid in the auction '{auction.title}'.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[previous_bid.bidder.email],
            fail_silently=True
        )
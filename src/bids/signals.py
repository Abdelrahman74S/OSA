from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Bid ,AutoBid
from django.core.mail import send_mail
from django.conf import settings
from .services import place_bid_service
import threading

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


_local = threading.local()

@receiver(post_save, sender=AutoBid)
def auto_bid_created(sender, instance, created, **kwargs):
    if not created or not instance.is_active:
        return

    auction = instance.auction
    bidder = instance.bidder
    max_amount = instance.max_amount

    if not auction.is_active:
        return

    current_price = auction.current_price
    bid_increment = auction.bid_increment
    min_valid_bid = current_price + bid_increment

    if max_amount >= min_valid_bid:
        if not getattr(_local, 'resolving_auto_bids', False):
            _local.resolving_auto_bids = True
            try:
                place_bid_service(auction.id, bidder, min_valid_bid)
            finally:
                _local.resolving_auto_bids = False

# celery
@receiver(post_save, sender=Bid)
def trigger_auto_bids_on_new_bid(sender, instance, created, **kwargs):
    if not created or not instance.is_valid:
        return

    if getattr(_local, 'resolving_auto_bids', False):
        return

    _local.resolving_auto_bids = True
    try:
        auction = instance.auction
        
        while True:
            auction.refresh_from_db()
            
            highest_bid = Bid.objects.filter(auction=auction, is_valid=True).order_by('-amount').first()
            if not highest_bid:
                break
                
            min_valid_bid = highest_bid.amount + auction.bid_increment
            
            eligible_auto_bids = AutoBid.objects.filter(
                auction=auction,
                is_active=True,
                max_amount__gte=min_valid_bid
            ).exclude(bidder=highest_bid.bidder).order_by('-max_amount')
            
            if not eligible_auto_bids.exists():
                break
                
            top_auto_bid = eligible_auto_bids.first()
            place_bid_service(auction.id, top_auto_bid.bidder, min_valid_bid)
            
    finally:
        _local.resolving_auto_bids = False
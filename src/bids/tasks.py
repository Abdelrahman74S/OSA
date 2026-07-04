from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from .models import Bid, AutoBid
from .services import place_bid_service
from auctions.models import AuctionListing
import threading
_local = threading.local()


@shared_task
def notify_new_bid(auction_id):

    auction = AuctionListing.objects.get(id=auction_id)
    bid = Bid.objects.filter(auction=auction, is_valid=True).order_by('-amount').first()
    seller_email = auction.seller.email

    send_mail(
        subject=f"New bid on your item '{auction.title}'",
        message=f"Hi {auction.seller.username}, a new bid of {auction.current_price} has been placed on your item '{auction.title}'.",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[seller_email],
        fail_silently=True
    )

    previous_bid = (
        Bid.objects.filter(auction=auction, is_valid=True)
        .exclude(id=bid.id)
        .order_by('-amount')
        .first()
    )

    if previous_bid and previous_bid.bidder != bid.bidder:
        send_mail(
            subject=f"Your bid on '{auction.title}' has been outbid",
            message=f"Hi {previous_bid.bidder.username}, your previous bid of {previous_bid.amount} has been outbid in the auction '{auction.title}'.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[previous_bid.bidder.email],
            fail_silently=True
        )



def resolve_auto_bids_loop(auction):
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


@shared_task
def auto_bid_created_task(auto_bid_id):
    try:
        auto_bid_obj = AutoBid.objects.get(id=auto_bid_id)
    except AutoBid.DoesNotExist:
        return

    auction = auto_bid_obj.auction
    bidder = auto_bid_obj.bidder
    max_amount = auto_bid_obj.max_amount

    if not auction.is_active:
        return

    _local.resolving_auto_bids = True
    try:
        current_price = auction.current_price
        bid_increment = auction.bid_increment
        min_valid_bid = current_price + bid_increment

        if max_amount >= min_valid_bid:
            place_bid_service(auction.id, bidder, min_valid_bid)
            resolve_auto_bids_loop(auction)
    finally:
        _local.resolving_auto_bids = False


@shared_task
def trigger_auto_bids_on_new_bid_task(auction_id):
    try:
        auction = AuctionListing.objects.get(id=auction_id)
    except AuctionListing.DoesNotExist:
        return

    _local.resolving_auto_bids = True
    try:
        resolve_auto_bids_loop(auction)
    finally:
        _local.resolving_auto_bids = False
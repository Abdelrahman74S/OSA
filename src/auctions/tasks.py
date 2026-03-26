from celery import shared_task
from django.utils import timezone
from .models import AuctionListing
from bids.models import Bid #
from django.db import transaction

@shared_task
def close_expired_auctions():

    now = timezone.now()
    expired_auctions = AuctionListing.objects.filter(
        status='ACTIVE', 
        end_time__lte=now
    )

    for auction in expired_auctions:
        with transaction.atomic():
            auction = AuctionListing.objects.select_for_update().get(pk=auction.id)
            
            if auction.status != 'ACTIVE':
                continue

            highest_bid = Bid.objects.filter(
                auction=auction, 
                is_valid=True
            ).order_by('-amount').first()

            if highest_bid:
                if auction.reserve_price is None or highest_bid.amount >= auction.reserve_price:
                    auction.winner = highest_bid.bidder

            auction.status = 'ENDED' #
            auction.save()
            
    return f"Closed {expired_auctions.count()} auctions."
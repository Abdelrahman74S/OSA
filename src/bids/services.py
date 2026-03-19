# services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import AuctionListing, Bid

def place_bid_service(auction_id, user, bid_amount):

    with transaction.atomic():
        auction = AuctionListing.objects.select_for_update().get(pk=auction_id)
        
        if bid_amount <= auction.current_price:
            raise ValidationError("Bid must be higher than the current price.")
            
        Bid.objects.create(auction=auction, bidder=user, amount=bid_amount)
        
        auction.current_price = bid_amount
        auction.highest_bidder = user
        auction.save()
        
    return auction
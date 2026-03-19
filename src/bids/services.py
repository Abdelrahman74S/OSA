from django.utils import timezone
from django.core.exceptions import ValidationError
from auctions.models import AuctionListing
from .models import Bid

def place_bid_service(auction_id, user, amount):

    try:
        auction = AuctionListing.objects.get(pk=auction_id)
    except AuctionListing.DoesNotExist:
        raise ValidationError({"auction": "Auction not found."})

    if not auction.is_active:
        raise ValidationError({"auction": "Auction is not active."})

    if auction.seller == user:
        raise ValidationError({"bidder": "The seller cannot bid on their own auction."})

    if timezone.now() > auction.end_time:
        if auction.winner is None:
            highest_bid = Bid.objects.filter(auction=auction, is_valid=True).order_by('-amount').first()
            if highest_bid:
                auction.winner = highest_bid.bidder
                auction.status = AuctionListing.Status.COMPLETED
                auction.save()
        raise ValidationError({"auction": "Auction has ended. No more bids allowed."})

    min_bid = auction.current_price + auction.bid_increment
    if amount < min_bid:
        raise ValidationError(
            {"amount": f"Minimum bid is {min_bid} (current price + increment)."}
        )

    bid = Bid.objects.create(
        auction=auction,
        bidder=user,
        amount=amount
    )

    auction.current_price = bid.amount
    auction.save()

    return bid
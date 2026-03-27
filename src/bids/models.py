from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid
from django.core.validators import MinValueValidator
from auctions.models import AuctionListing

class Bid(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    auction = models.ForeignKey(
        'auctions.AuctionListing',
        on_delete=models.CASCADE,
        related_name='bids'
    )
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bidder_bids'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2 , validators=[MinValueValidator(0.00)])
    bid_time = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)

    class Meta:
        ordering = ['-amount']
        indexes = [
            models.Index(fields=['auction', 'is_valid']),  
            models.Index(fields=['bidder']),
            models.Index(fields=['auction', '-amount']),    
        ]

    def clean(self):
        errors = {}

        if self.bidder_id == self.auction.seller_id:
            errors['bidder'] = "The seller cannot bid on their own auction."
            
        if not self.auction.is_active:
            errors['auction'] = "Bids can only be placed on active auctions."

        if self.amount is not None and self.amount <= self.auction.current_price:
            errors['amount'] = (
                f"Bid amount must be greater than the current price "
                f"({self.auction.current_price})."
            )

        min_valid_bid = self.auction.current_price + self.auction.bid_increment
        if self.amount is not None and self.amount < min_valid_bid:
            errors['amount'] = (
                f"Bid amount must be at least {min_valid_bid} "
                f"(current price + bid increment)."
            )

        if errors:
            raise ValidationError(errors)


    def __str__(self):
        return f"{self.bidder} → {self.auction} @ {self.amount}"


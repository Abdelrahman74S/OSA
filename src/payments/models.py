from django.utils import timezone
from django.db import models
from auctions.models import AuctionListing
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.core.exceptions import ValidationError
import uuid

class Transaction(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        DISPUTED = 'DISPUTED', 'Disputed'
        COMPLETED = 'COMPLETED', 'Completed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    auction = models.OneToOneField(
        AuctionListing,
        on_delete=models.CASCADE,
        related_name='transaction'
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions_bought'
    )

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions_sold'
    )

    final_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.0)]
    )

    platform_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.0)],
        editable=False
    )

    seller_earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.0)],
        editable=False
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    tracking_number = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.final_price = self.auction.current_price
        self.platform_fee = self.final_price * Decimal('0.05')
        self.seller_earnings = self.final_price - self.platform_fee

        super().save(*args, **kwargs)
        
    def clean(self):
        if self.buyer == self.seller:
            raise ValidationError("Buyer cannot be the seller")

    def can_transition(self, new_status):
        allowed = {
            self.Status.PENDING: [self.Status.PAID],
            self.Status.PAID: [self.Status.SHIPPED],
            self.Status.SHIPPED: [self.Status.DELIVERED],
            self.Status.DELIVERED: [self.Status.COMPLETED],
        }
        return new_status in allowed.get(self.status, [])
    
    def mark_as_paid(self):
        if not self.can_transition(self.Status.PAID):
            raise ValidationError("Invalid status transition")
    
        self.status = self.Status.PAID
        self.paid_at = timezone.now()
        self.save()
    
    def mark_as_shipped(self):
        if not self.can_transition(self.Status.SHIPPED):
            raise ValidationError("Invalid status transition")
    
        self.status = self.Status.SHIPPED
        self.shipped_at = timezone.now()
        self.save()
    
    def mark_as_delivered(self):
        if not self.can_transition(self.Status.DELIVERED):
            raise ValidationError("Invalid status transition")
    
        self.status = self.Status.DELIVERED
        self.delivered_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"Transaction #{self.id} - {self.status}"
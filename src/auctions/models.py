from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
from celery import shared_task

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='category_icons/', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)


    def __str__(self):
        return self.name


class AuctionListing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('ENDED', 'Ended'),
        ('CANCELLED', 'Cancelled'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='auctions'
    )

    # Pricing
    starting_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    reserve_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bid_increment = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)

    # Timing
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    payment_due_by = models.DateTimeField(null=True, blank=True)

    # Status & Results
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_auctions'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'end_time']),   
            models.Index(fields=['seller']),                
            models.Index(fields=['category']),              
            models.Index(fields=['start_time', 'end_time']),
        ]
        
    @shared_task
    def close_expired_auctions():
        from bids.models import Bid
        expired_auctions = AuctionListing.objects.filter(
            status=AuctionListing.Status.ACTIVE,
            end_time__lte=timezone.now()
        )
    
        for auction in expired_auctions:
            highest_bid = (
                Bid.objects.filter(auction=auction, is_valid=True)
                .order_by('-amount')
                .first()
            )
    
            if highest_bid:
                auction.winner = highest_bid.bidder
    
            auction.status = AuctionListing.Status.ENDED
            auction.save()

    def clean(self):
        if self.current_price < self.starting_price:
            raise ValidationError("Current price must be >= starting price.")
        if self.bid_increment <= 0:
            raise ValidationError("Bid increment must be positive.")
        if self.starting_price <= 0:
            raise ValidationError("Starting price must be positive.")
        
    def __str__(self):
        return self.title

    @property
    def is_active(self):
        return self.status == 'ACTIVE' and self.start_time <= timezone.now() <= self.end_time

class AuctionImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auction = models.ForeignKey(AuctionListing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='auctions/%Y/%m/')
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['auction', 'is_primary']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['auction'],
                condition=models.Q(is_primary=True),
                name='unique_primary_image_per_auction'
            )
        ]
        

class Watchlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watchlist'
    )
    auction = models.ForeignKey(
        'AuctionListing',
        on_delete=models.CASCADE,
        related_name='watchers'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['auction']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'auction'],
                name='unique_user_auction_watchlist'
            )
        ]

    def __str__(self):
        return f"{self.user} watching {self.auction}"
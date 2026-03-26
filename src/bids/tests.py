from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from auctions.models import AuctionListing, Category
from .services import place_bid_service
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class BidServiceTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller", 
            email="abdoelashri841@gmail.com", 
            password="password"
        )
        self.bidder = User.objects.create_user(
            username="bidder", 
            email="abdobo841@gmail.com", 
            password="password"
        )
        
        self.category = Category.objects.create(name="Electronics")
        
        self.auction = AuctionListing.objects.create(
            title="Laptop",
            description="Macbook",
            seller=self.seller,
            category=self.category,
            starting_price=Decimal("1000.00"),
            current_price=Decimal("1000.00"),
            bid_increment=Decimal("50.00"),
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(days=1),
            status='ACTIVE'
        )

    def test_place_valid_bid(self):
        place_bid_service(self.auction.id, self.bidder, Decimal("1100.00"))
        
        self.auction.refresh_from_db()
        
        self.assertEqual(self.auction.current_price, Decimal("1100.00"))
        
        self.assertEqual(self.auction.highest_bidder, self.bidder)

    def test_place_low_bid_raises_error(self):
        with self.assertRaises(ValidationError):
            place_bid_service(self.auction.id, self.bidder, Decimal("1020.00"))
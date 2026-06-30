from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from auctions.models import AuctionListing, Category
from django.contrib.auth import get_user_model
from bids.services import place_bid_service

User = get_user_model()

class PlaceBidServiceTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
        username="seller", 
        email="seller@example.com", 
        password="pass"
        )
        self.bidder = User.objects.create_user(
            username="bidder", 
            email="bidder@example.com", 
            password="pass"
        )
        self.category = Category.objects.create(name="Tech")

        self.auction = AuctionListing.objects.create(
            title="Laptop",
            seller=self.seller,
            category=self.category,
            starting_price=Decimal("1000.00"),
            current_price=Decimal("1000.00"),
            bid_increment=Decimal("10.00"),
            status='ACTIVE', 
            start_time=timezone.now() - timezone.timedelta(hours=1), 
            end_time=timezone.now() + timezone.timedelta(hours=1)   
        )
        
    def test_place_bid_success(self):
        new_bid_amount = Decimal("1050.00")
        
        place_bid_service(self.auction.id, self.bidder, new_bid_amount)
        
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.current_price, new_bid_amount)
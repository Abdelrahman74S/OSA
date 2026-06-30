from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Category, AuctionListing, AuctionImage, Watchlist
from django.urls import reverse
from django.utils import timezone
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.db import IntegrityError

User = get_user_model()

def generate_test_image():
    img = BytesIO(
        b"GIF89a\x01\x00\x01\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00"
        b"\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01\x00\x00"
    )
    img.name = "test.jpg"

    return SimpleUploadedFile(
        name=img.name,
        content=img.getvalue(),
        content_type="image/jpeg"
    )



class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Smart Phones")

    def test_category_creation(self):
        self.assertEqual(self.category.name, "Smart Phones")
        self.assertEqual(self.category.slug, "smart-phones")
        self.assertEqual(str(self.category), "Smart Phones")
    
    def test_category_unique_slug_generation(self):
        Category.objects.create(name="Electronics")
        duplicate_category = Category.objects.create(name="Electronics")
        duplicate_category2 = Category.objects.create(name="Electronics")
        
        self.assertEqual(duplicate_category.slug, "electronics-1")
        self.assertEqual(duplicate_category2.slug, "electronics-2")

class AuctionListingModelTest(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", password="testpass")
        cls.category = Category.objects.create(name="Laptops")
        cls.auction = AuctionListing.objects.create(
            title="MacBook Pro",
            description="A great laptop",
            seller=cls.user,
            category=cls.category,
            starting_price=999.99,
            current_price=999.99,
            reserve_price=1200.00,
            bid_increment=50.00,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(days=7),
            payment_due_by=timezone.now() + timezone.timedelta(days=10),
        )

    def test_auction_listing_creation(self):
        self.assertEqual(self.auction.title, "MacBook Pro")
        self.assertEqual(self.auction.description, "A great laptop")
        self.assertEqual(self.auction.seller, self.user)
        self.assertEqual(self.auction.category, self.category)
        self.assertEqual(self.auction.starting_price, 999.99)
        self.assertEqual(self.auction.current_price, 999.99)
        self.assertEqual(self.auction.reserve_price, 1200.00)
        self.assertEqual(self.auction.bid_increment, 50.00)
    
    def test_auction_is_active_property(self):
        self.assertFalse(self.auction.is_active) 
        
        self.auction.status = 'ACTIVE'
        self.auction.save()
        self.assertTrue(self.auction.is_active)

        self.auction.end_time = timezone.now() - timezone.timedelta(days=1)
        self.auction.save()
        self.assertFalse(self.auction.is_active)

    def test_primary_image_constraint(self):
        AuctionImage.objects.create(auction=self.auction, image=generate_test_image(), is_primary=True)
        
        with self.assertRaises(IntegrityError):
            AuctionImage.objects.create(auction=self.auction, image=generate_test_image(), is_primary=True)

class AuctionListingViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user = User.objects.create_user(username="testuser", password="testpass")
        cls.category = Category.objects.create(name="Tablets")
        cls.auction = AuctionListing.objects.create(
            title="iPad Pro",
            description="A powerful tablet",
            seller=cls.user,
            category=cls.category,
            starting_price=799.99,
            current_price=799.99,
            reserve_price=1000.00,
            bid_increment=25.00,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(days=5),
            payment_due_by=timezone.now() + timezone.timedelta(days=8),
        )
        
        cls.auction_detail_url = reverse('auction-detail', kwargs={'pk': cls.auction.id})
        cls.auction_url = reverse('auction-list-create')
        
    def test_list_auction_listings(self):
        response = self.client.get(self.auction_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "iPad Pro")
        
    def test_retrieve_auction_listing(self):
        response = self.client.get(self.auction_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], "iPad Pro")
        
    def test_create_auction_listing_unauthenticated(self):
        data = {
            "title": "Surface Pro",
            "description": "A versatile tablet",
            "category": self.category.id,
            "starting_price": 899.99,
            "reserve_price": 1100.00,
            "bid_increment": 30.00,
            "start_time": timezone.now(),
            "end_time": timezone.now() + timezone.timedelta(days=7),
            "payment_due_by": timezone.now() + timezone.timedelta(days=10),
        }
        response = self.client.post(self.auction_url, data, format='json')
        self.assertEqual(response.status_code, 401)
    
    
    def test_auction_validation(self):
        self.auction.current_price = 100.00 
        with self.assertRaises(ValidationError):
            self.auction.clean()
        
        self.auction.bid_increment = -5.00
        with self.assertRaises(ValidationError):
            self.auction.clean()


class AuctionImageModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", password="testpass")
        cls.category = Category.objects.create(name="Cameras")
        cls.auction = AuctionListing.objects.create(
            title="Canon EOS",
            description="A high-quality camera",
            seller=cls.user,
            category=cls.category,
            starting_price=499.99,
            current_price=499.99,
            reserve_price=700.00,
            bid_increment=20.00,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(days=3),
            payment_due_by=timezone.now() + timezone.timedelta(days=6),
        )
        cls.image = AuctionImage.objects.create(
            auction=cls.auction,
            image = generate_test_image(),
        )

    def test_auction_image_creation(self):
        self.assertEqual(self.image.auction, self.auction)
        self.assertTrue(self.image.image)
        
        self.assertIn("test", self.image.image.name)
        
        self.assertTrue(self.image.image.name.endswith(".jpg"))
    
        self.assertTrue(self.image.image.name.startswith("auctions/"))

class WatchlistTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="watcher", password="pass")
        self.category = Category.objects.create(name="Items")
        self.auction = AuctionListing.objects.create(
            title="Item 1", seller=self.user, category=self.category,
            starting_price=10, current_price=10, start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(days=1)
        )

    def test_watchlist_unique_constraint(self):
        Watchlist.objects.create(user=self.user, auction=self.auction)
        
        with self.assertRaises(IntegrityError):
            Watchlist.objects.create(user=self.user, auction=self.auction)
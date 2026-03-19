from .models import Category, AuctionListing, AuctionImage , Watchlist
from .serializers import (
        AuctionListingSerializer, AuctionImageSerializer, 
        CategorySerializer, WatchlistSerializer
)
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    DestroyAPIView
)
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter , OrderingFilter
from django.contrib.auth import get_user_model

User = get_user_model()


# ──────────────────────────────────────────
# Category Views
# ──────────────────────────────────────────

class ListCreateCategory(ListCreateAPIView):
    queryset = Category.objects.all()       
    serializer_class = CategorySerializer
    filter_backends = [SearchFilter]
    search_fields = ['name']
    
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [AllowAny()]


class RetrieveUpdateDestroyCategory(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()         
    serializer_class = CategorySerializer
    lookup_field = "slug"                     

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdminUser()]
        return [AllowAny()]


# ──────────────────────────────────────────
# AuctionListing Views
# ──────────────────────────────────────────

class ListCreateAuctionListing(ListCreateAPIView):
    serializer_class = AuctionListingSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_fields = [
        'seller', 'starting_price', 
        'current_price','bid_increment',
        'status', 
    ]
    search_fields = ['title', 'description' , 'seller__username' ,'winner__username']
    ordering_fields = ['created_at','starting_price','bid_increment']
    
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        qs = AuctionListing.objects.select_related(
            "seller", "category", "winner"
        ).prefetch_related("images")

        return qs

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)                      


class RetrieveUpdateDestroyAuctionListing(RetrieveUpdateDestroyAPIView):
    serializer_class = AuctionListingSerializer
    lookup_field = "pk"                       

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        return AuctionListing.objects.select_related(
            "seller", "category", "winner"
        ).prefetch_related("images")

    def perform_update(self, serializer):
        if serializer.instance.seller != self.request.user:
            raise PermissionDenied("You do not have the authority to modify this auction.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.seller != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("You do not have the authority to modify this auction.")
        instance.delete()


# ──────────────────────────────────────────
# AuctionImage Views
# ──────────────────────────────────────────
class ListCreateAuctionImage(ListCreateAPIView):
    serializer_class = AuctionImageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  

    def get_queryset(self):
        return AuctionImage.objects.filter(
            auction_id=self.kwargs["auction_pk"]
        )

    def perform_create(self, serializer):
        auction = AuctionListing.objects.get(pk=self.kwargs["auction_pk"])
        if auction.seller != self.request.user:
            raise PermissionDenied("Only the seller can add pictures.")
        serializer.save(auction=auction)


class RetrieveUpdateDestroyAuctionImage(RetrieveUpdateDestroyAPIView):
    serializer_class = AuctionImageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return AuctionImage.objects.filter(
            auction_id=self.kwargs["auction_pk"]
        ).select_related("auction__seller")     

    def _check_ownership(self, image):
        if image.auction.seller != self.request.user:
            raise PermissionDenied("Only the seller can modify this image.")

    def perform_update(self, serializer):      
        self._check_ownership(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):       
        self._check_ownership(instance)
        instance.delete()
        
        

# ══════════════════════════════════════════
# Watchlist Views
# ══════════════════════════════════════════

class ListCreateWatchlist(ListCreateAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_fields = [
            'auction__seller', 'auction__starting_price', 
            'auction__current_price', 'auction__status', 'added_at'
    ]
    search_fields = [
            'auction__title', 'auction__description', 
            'auction__seller__username', 'auction__winner__username'
    ]
    ordering_fields = ['added_at','auction__starting_price','auction__bid_increment']

    def get_queryset(self):
        return (
            Watchlist.objects
            .filter(user=self.request.user)
            .select_related("auction__seller", "auction__category")
            .prefetch_related("auction__images")
        )
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DestroyWatchlist(DestroyAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You cannot remove items from another user's watchlist.")
        instance.delete()



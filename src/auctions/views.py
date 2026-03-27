from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.contrib.auth import get_user_model

from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    DestroyAPIView,
    RetrieveAPIView
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Category, AuctionListing, AuctionImage, Watchlist
from .serializers import (
    AuctionImageSerializer, 
    AuctionListSerializer,
    AuctionDetailSerializer,
    AuctionCreateSerializer,
    CategorySerializer, 
    WatchlistSerializer
)
from .Permissions import IsSellerOrReadOnly
from .filter import AuctionFilter
from django.db.models import Subquery, OuterRef


User = get_user_model()


# ──────────────────────────────────────────
#  Functions for Cache Keys
# ──────────────────────────────────────────
def get_category_list_cache_key():
    return "category_list_all"

def get_auction_list_cache_key(query_params=None):
    if query_params:
        param_str = "_".join([f"{k}_{v}" for k, v in sorted(query_params.items())])
        return f"auction_list_{param_str}"
    return "auction_list_all"

def get_auction_images_cache_key(auction_pk):
    return f"auction_images_{auction_pk}"

def get_watchlist_cache_key(user_id):
    return f"watchlist_user_{user_id}"


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

    def list(self, request, *args, **kwargs):
        cache_key = get_category_list_cache_key()
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 3600)  
        return response

    def perform_create(self, serializer):
        instance = serializer.save()
        cache.delete(get_category_list_cache_key())
        return instance


class RetrieveUpdateDestroyCategory(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdminUser()]
        return [AllowAny()]

    def perform_update(self, serializer):
        instance = serializer.save()
        cache.delete(get_category_list_cache_key())
        return instance

    def perform_destroy(self, instance):
        cache.delete(get_category_list_cache_key())
        instance.delete()


# ──────────────────────────────────────────
# AuctionListing Views
# ──────────────────────────────────────────

class ListCreateAuctionListing(ListCreateAPIView):
    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['seller', 'status', 'category']
    search_fields = ['title', 'description', 'seller__username']
    ordering_fields = ['created_at', 'starting_price']
    filterset_class = AuctionFilter

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AuctionCreateSerializer
        return AuctionListSerializer

    def get_permissions(self):
        return [IsAuthenticated()] if self.request.method == "POST" else [AllowAny()]

    def get_queryset(self):
        from bids.models import Bid
        highest_bidder_subquery = Bid.objects.filter(
            auction=OuterRef('pk'),
            is_valid=True
        ).order_by('-amount').values('bidder__username')[:1] 

        return AuctionListing.objects.select_related("seller", "category")\
            .prefetch_related("images")\
            .annotate(
                highest_bidder_username=Subquery(highest_bidder_subquery)
            )

    def list(self, request, *args, **kwargs):
        cache_key = get_auction_list_cache_key(request.query_params)
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 300)
        return response

    def perform_create(self, serializer):
        instance = serializer.save(
            seller=self.request.user,
            current_price=serializer.validated_data['starting_price']
        )
        self._clear_auction_list_cache()
        return instance

    def _clear_auction_list_cache(self):
        keys_to_delete = [
            get_auction_list_cache_key(),
            get_auction_list_cache_key({'status': 'active'}),
            get_auction_list_cache_key({'ordering': 'created_at'}),
        ]
        for key in keys_to_delete:
            cache.delete(key)
        try:
            cache.delete_pattern("auction_list_*")
        except AttributeError:
            pass


class RetrieveUpdateDestroyAuctionListing(RetrieveUpdateDestroyAPIView):

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']: 
            return [IsSellerOrReadOnly()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AuctionCreateSerializer
        return AuctionDetailSerializer

    def get_queryset(self):
        return AuctionListing.objects.select_related(
            "seller", "category", "winner"
        ).prefetch_related("images", "bids__bidder")

    def perform_update(self, serializer):
        instance = serializer.save()
        cache.delete(get_auction_list_cache_key())
        cache.delete(f"auction_list_{instance.id}")  
        return instance

    def perform_destroy(self, instance):
        cache.delete(get_auction_list_cache_key())
        instance.delete()


# ──────────────────────────────────────────
# AuctionImage Views 
# ──────────────────────────────────────────

class ListCreateAuctionImage(ListCreateAPIView):
    serializer_class = AuctionImageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return AuctionImage.objects.filter(
            auction_id=self.kwargs["auction_pk"]
        ).select_related('auction')

    def list(self, request, *args, **kwargs):
        auction_pk = self.kwargs["auction_pk"]
        cache_key = get_auction_images_cache_key(auction_pk)
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 600)  
        return response

    def perform_create(self, serializer):
        auction = get_object_or_404(AuctionListing, pk=self.kwargs["auction_pk"])
        if auction.seller != self.request.user:
            raise PermissionDenied("Only the seller can add pictures.")
        
        instance = serializer.save(auction=auction)
        cache.delete(get_auction_images_cache_key(auction.id))
        return instance


class RetrieveUpdateDestroyAuctionImage(RetrieveUpdateDestroyAPIView):
    serializer_class = AuctionImageSerializer
    permission_classes = [IsAuthenticated, IsSellerOrReadOnly]
    lookup_field = "pk"

    def get_queryset(self):
        return AuctionImage.objects.filter(
            auction_id=self.kwargs["auction_pk"]
        ).select_related('auction')

    def perform_update(self, serializer):
        instance = serializer.save()
        cache.delete(get_auction_images_cache_key(instance.auction.id))
        return instance

    def perform_destroy(self, instance):
        auction_id = instance.auction.id
        instance.delete()
        cache.delete(get_auction_images_cache_key(auction_id))


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
    ordering_fields = ['added_at', 'auction__starting_price', 'auction__bid_increment']

    def get_queryset(self):
        return Watchlist.objects.filter(
            user=self.request.user
        ).select_related(
            "auction__seller", "auction__category"
        ).prefetch_related("auction__images")

    def list(self, request, *args, **kwargs):
        cache_key = get_watchlist_cache_key(request.user.id)
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 60)  
        return response

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        cache.delete(get_watchlist_cache_key(self.request.user.id))
        return instance


class DestroyWatchlist(DestroyAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You cannot remove items from another user's watchlist.")
        
        user_id = instance.user.id
        instance.delete()
        cache.delete(get_watchlist_cache_key(user_id))
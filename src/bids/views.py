from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError as APIValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Bid
from .serializers import BidSerializer
from .models import AuctionListing
from .services import place_bid_service

class ListCreateBid(ListCreateAPIView):
    serializer_class = BidSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filterset_fields = [
        'auction__seller', 'auction__starting_price', 
        'auction__current_price', 'auction__status', 
        'bid_time','bidder','amount','is_valid'
    ]
    search_fields = [
        'auction__title', 'auction__description', 
        'auction__seller__username', 'bidder__username'
    ]
    ordering_fields = ['bid_time','auction__starting_price','auction__bid_increment' ,'amount']

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        return (
            Bid.objects
            .filter(auction_id=self.kwargs["auction_pk"], is_valid=True)
            .select_related("bidder", "auction")
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        auction = AuctionListing.objects.get(pk=self.kwargs["auction_pk"])
        context['auction'] = auction
        return context

    def perform_create(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise APIValidationError(
                detail=e.message_dict if hasattr(e, 'message_dict') else e.messages
            )


class RetrieveBid(RetrieveAPIView):
    serializer_class = BidSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Bid.objects.filter(
            auction_id=self.kwargs["auction_pk"]
        ).select_related("bidder", "auction")
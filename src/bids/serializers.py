from attr import attrs
from jsonschema import ValidationError
from rest_framework import serializers
from .models import AutoBid, Bid
from .services import place_bid_service

class BidSerializer(serializers.ModelSerializer):
    bidder = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Bid
        fields = [
            "id",
            "auction",
            "bidder",
            "amount",
            "bid_time",
            "is_valid",
        ]
        read_only_fields = ["id", "bidder", "bid_time", "is_valid"]

    def validate(self, data):
        auction = data.get('auction') or self.context.get('auction')
        if not auction:
            raise serializers.ValidationError({"auction": "Auction not found."})

        amount = data.get('amount')
        user = self.context['request'].user

        if auction.seller == user:
            raise serializers.ValidationError(
                {"bidder": "The seller cannot bid on their own auction."}
            )

        if not auction.is_active:
            raise serializers.ValidationError(
                {"auction": "Bids can only be placed on active auctions."}
            )

        min_valid_bid = auction.current_price + auction.bid_increment
        if amount < min_valid_bid:
            raise serializers.ValidationError(
                {"amount": f"Minimum bid is {min_valid_bid} (current price + increment)."}
            )

        return data
    
    def create(self, validated_data):
        auction = validated_data.get('auction') or self.context['auction']
        user = self.context['request'].user
        amount = validated_data['amount']
    
        bid = place_bid_service(auction.id, user, amount)
        return bid


class AutoBidSerializer(serializers.ModelSerializer):
    bidder = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = AutoBid  
        fields = [
            "id",
            "auction",
            "bidder",
            "max_amount",  
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "bidder", "created_at"]
        
    def validate(self, data):
        errors = {}
        auction = data.get('auction')
        max_amount = data.get('max_amount')  
        
        request = self.context.get('request')
        bidder = request.user if request else None
        
        if not bidder:
            raise serializers.ValidationError({"detail": "User must be authenticated."})

        if auction and bidder == auction.seller:
            errors['bidder'] = "The seller cannot set an auto-bid on their own auction."
            
        if auction and not auction.is_active:
            errors['auction'] = "Auto-bids can only be set on active auctions."

        if max_amount is not None and auction and max_amount <= auction.current_price:
            errors['max_amount'] = f"Auto-bid max amount must be greater than the current price ({auction.current_price})."

        if not self.instance and auction:
            if AutoBid.objects.filter(bidder=bidder, auction=auction).exists():
                errors['auction'] = "You already have an auto-bid configuration for this auction. Please update it instead."

        if errors:
            raise serializers.ValidationError(errors)

        return data
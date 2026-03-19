from rest_framework import serializers
from .models import Bid
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
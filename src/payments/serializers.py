from rest_framework import serializers
from .models import Transaction
from accounts.serializers import Userserializers 
from auctions.serializers import AuctionListSerializer

class TransactionSerializer(serializers.ModelSerializer):
    buyer_details = Userserializers(source='buyer', read_only=True)
    seller_details = Userserializers(source='seller', read_only=True)
    auction_details = AuctionListSerializer(source='auction', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'auction', 'buyer', 'seller', 'final_price',
            'platform_fee', 'seller_earnings', 'status',
            'paid_at', 'shipped_at', 'delivered_at',
            'tracking_number', 'created_at'
        ]
        read_only_fields = [
            'final_price', 'platform_fee', 'seller_earnings',
            'paid_at', 'shipped_at', 'delivered_at', 'created_at'
        ]

class TransactionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['tracking_number']

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
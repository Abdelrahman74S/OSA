from rest_framework import serializers
from django.utils import timezone
from .models import Category, AuctionListing, AuctionImage
from .models import Watchlist


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "subcategories",
            "description",
            "icon",
        ]
        read_only_fields = ["slug"]

    def validate(self, data):
        instance = self.instance
        parent = data.get('parent')

        if instance and parent and parent.pk == instance.pk:
            raise serializers.ValidationError(
                {"parent": "A category cannot be its own parent."}
            )
        return data


class AuctionImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuctionImage
        fields = [
            "id",
            "image",
            "order",
            "is_primary",
            "uploaded_at",
        ]
        read_only_fields = ["id","uploaded_at"]


class AuctionListingSerializer(serializers.ModelSerializer):
    images = AuctionImageSerializer(many=True, read_only=True)
    is_active = serializers.SerializerMethodField()

    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )
    seller = serializers.PrimaryKeyRelatedField(read_only=True)
    winner = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = AuctionListing
        fields = [
            "id",
            "title",
            "description",
            "category",
            "seller",
            # Pricing
            "starting_price",
            "current_price",
            "reserve_price",
            "bid_increment",
            # Timing
            "start_time",
            "end_time",
            "payment_due_by",
            # Status & Results
            "status",
            "winner",
            "is_active",
            # Meta
            "created_at",
            "updated_at",
            "images",
        ]
        read_only_fields = [ "id", "current_price", "winner", "created_at", "updated_at"]

    def get_is_active(self, obj):
        return obj.is_active

    def validate_starting_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Starting price must be greater than zero.")
        return value

    def validate_bid_increment(self, value):
        if value <= 0:
            raise serializers.ValidationError("Bid increment must be greater than zero.")
        return value

    def validate(self, data):
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        starting_price = data.get('starting_price')
        reserve_price = data.get('reserve_price')

        if start_time and end_time:
            if end_time <= start_time:
                raise serializers.ValidationError(
                    {"end_time": "End time must be after the start time."}
                )
            if not self.instance and start_time < timezone.now():
                raise serializers.ValidationError(
                    {"start_time": "Start time cannot be in the past."}
                )

        if reserve_price is not None and starting_price is not None:
            if reserve_price < starting_price:
                raise serializers.ValidationError(
                    {"reserve_price": "Reserve price cannot be less than starting price."}
                )

        return data

    def create(self, validated_data):
        validated_data['current_price'] = validated_data['starting_price']
        validated_data['seller'] = self.context['request'].user
        return super().create(validated_data)
    
#--------------------

class WatchlistSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Watchlist
        fields = [
            "id",
            "user",
            "auction",
            "added_at",
        ]
        read_only_fields = ["id", "user", "added_at"]

    def validate(self, data):
        user = self.context['request'].user
        auction = data.get('auction')


        if auction.seller == user:
            raise serializers.ValidationError(
                {"auction": "You cannot watch your own auction."}
            )

        if Watchlist.objects.filter(user=user, auction=auction).exists():
            raise serializers.ValidationError(
                {"auction": "This auction is already in your watchlist."}
            )

        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

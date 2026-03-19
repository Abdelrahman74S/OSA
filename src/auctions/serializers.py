from rest_framework import serializers
from django.utils import timezone
from .models import Category, AuctionListing, AuctionImage
from .models import Watchlist
from bids.serializers import BidSerializer

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


#-----------------------------------
# Auction
#-----------------------------------
class AuctionImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuctionImage
        fields = ['id', 'image', 'is_primary', 'order']


class AuctionListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = AuctionListing
        fields = ['id', 'title', 'current_price', 'status', 'end_time', 'primary_image']

    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first() or obj.images.first()
        if img:
            return self.context['request'].build_absolute_uri(img.image.url)
        return None


class AuctionDetailSerializer(serializers.ModelSerializer):
    images = AuctionImageSerializer(many=True, read_only=True)
    bids = BidSerializer(many=True, read_only=True)
    seller = serializers.ReadOnlyField(source='seller.username')
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = AuctionListing
        fields = "__all__"

class AuctionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuctionListing
        fields = [
            "title", "description", "category", "starting_price", 
            "reserve_price", "bid_increment", "start_time", "end_time"
        ]

    def validate(self, data):
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})
        if not self.instance and data['start_time'] < timezone.now():
            raise serializers.ValidationError({"start_time": "Start time cannot be in the past."})
        return data
    
    
#--------------------
# Watchlist
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

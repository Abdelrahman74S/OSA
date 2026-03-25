import django_filters
from .models import AuctionListing

# class AuctionFilterStartingPrice(django_filters.FilterSet):
#     min_starting_price = django_filters.NumberFilter(field_name="starting_price", lookup_expr='gte')
#     max_starting_price = django_filters.NumberFilter(field_name="starting_price", lookup_expr='lte')

#     class Meta:
#         model = AuctionListing
#         fields = ['category']

# class AuctionFilterCurrentPrice(django_filters.FilterSet):
#     min_current_price = django_filters.NumberFilter(field_name="current_price", lookup_expr='gte')
#     max_current_price = django_filters.NumberFilter(field_name="current_price", lookup_expr='lte')

#     class Meta:
#         model = AuctionListing
#         fields = ['category']

# class AuctionFilterReservePrice(django_filters.FilterSet):
#     min_reserve_price = django_filters.NumberFilter(field_name="reserve_price", lookup_expr='gte')
#     max_reserve_price = django_filters.NumberFilter(field_name="reserve_price", lookup_expr='lte')

#     class Meta:
#         model = AuctionListing
#         fields = ['category']


class AuctionFilter(django_filters.FilterSet):
    bid_increment = django_filters.RangeFilter()
    reserve_price = django_filters.RangeFilter()
    starting_price = django_filters.RangeFilter()
    current_price = django_filters.RangeFilter()
    start_time = django_filters.DateTimeFromToRangeFilter()
    end_time = django_filters.DateTimeFromToRangeFilter()
    
    class Meta:
        model = AuctionListing
        fields = ['category']
from django.urls import path
from . import views

urlpatterns = [
    # Categories
    path("categories/", views.ListCreateCategory.as_view(), name="category-list-create"),
    path("categories/<slug:slug>/", views.RetrieveUpdateDestroyCategory.as_view(), name="category-detail"),

    # Auctions
    path("auctions/", views.ListCreateAuctionListing.as_view(), name="auction-list-create"),
    path("auctions/<uuid:pk>/", views.RetrieveUpdateDestroyAuctionListing.as_view(), name="auction-detail"),

    # Auction Images
    path("auctions/<uuid:auction_pk>/images/", views.ListCreateAuctionImage.as_view(), name="auction-image-list-create"),
    path("auctions/<uuid:auction_pk>/images/<uuid:pk>/", views.RetrieveUpdateDestroyAuctionImage.as_view(), name="auction-image-detail"),
    
    
    path(
        "auctions/watchlist/",
        views.ListCreateWatchlist.as_view(),
        name="watchlist-list-create"
    ),
    path(
        "auctions/watchlist/<uuid:pk>/",
        views.DestroyWatchlist.as_view(),
        name="watchlist-destroy"
    ),
]
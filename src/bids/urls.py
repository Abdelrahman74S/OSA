from django.urls import path
from . import views


urlpatterns = [
    path(
        "auctions/<uuid:auction_pk>/bids/",
        views.ListCreateBid.as_view(),
        name="bid-list-create"
    ),
    path(
        "auctions/<uuid:auction_pk>/bids/<uuid:pk>/",
        views.RetrieveBid.as_view(),
        name="bid-detail"
    ),
]
from django.contrib import admin
from .models import Category, AuctionListing, AuctionImage

admin.site.register(Category)
admin.site.register(AuctionListing)
admin.site.register(AuctionImage)
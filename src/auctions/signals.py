from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from auctions.models import AuctionListing, Category
from payments.models import Transaction

@receiver(post_save, sender=AuctionListing)
def create_transaction_on_auction_end(sender, instance, created, **kwargs):
    if instance.status == 'ENDED' and instance.winner and not hasattr(instance, 'transaction'):
        Transaction.objects.create(
            auction=instance,
            buyer=instance.winner,
            seller=instance.seller,
            final_price=instance.current_price
        )

@receiver(post_save, sender=AuctionListing)
def invalidate_auction_cache_on_save(sender, instance, **kwargs):
    try:
        cache.delete_pattern("auction_list_*")
    except AttributeError:
        cache.delete("auction_list_all")
    cache.delete(f"auction_list_{instance.id}")

@receiver(post_delete, sender=AuctionListing)
def invalidate_auction_cache_on_delete(sender, instance, **kwargs):
    try:
        cache.delete_pattern("auction_list_*")
    except AttributeError:
        cache.delete("auction_list_all")
    cache.delete(f"auction_list_{instance.id}")

@receiver(post_save, sender=Category)
def invalidate_category_cache_on_save(sender, instance, **kwargs):
    cache.delete("category_list_all")

@receiver(post_delete, sender=Category)
def invalidate_category_cache_on_delete(sender, instance, **kwargs):
    cache.delete("category_list_all")
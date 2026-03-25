from django.db.models.signals import post_save
from django.dispatch import receiver
from auctions.models import AuctionListing
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
        
# @receiver(post_save, sender=AuctionListing)
# def end_auction(sender, instance, created, **kwargs):
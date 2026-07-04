from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Bid, AutoBid
from .tasks import notify_new_bid, auto_bid_created_task, trigger_auto_bids_on_new_bid_task
import threading

# Thread-local for the HTTP request thread
_local = threading.local()

@receiver(post_save, sender=Bid)
def notify_on_new_bid(sender, instance, created, **kwargs):
    if not created:
        return
    transaction.on_commit(lambda: notify_new_bid.delay(instance.auction.id))


@receiver(post_save, sender=AutoBid)
def auto_bid_created(sender, instance, created, **kwargs):
    if not created or not instance.is_active:
        return
    transaction.on_commit(lambda: auto_bid_created_task.delay(instance.id))


@receiver(post_save, sender=Bid)
def trigger_auto_bids_on_new_bid(sender, instance, created, **kwargs):
    if not created or not instance.is_valid:
        return

    from .tasks import _local as tasks_local

    # If we are already resolving auto-bids in Celery worker thread or HTTP request thread, do not queue again
    if getattr(tasks_local, 'resolving_auto_bids', False) or getattr(_local, 'resolving_auto_bids', False):
        return

    transaction.on_commit(lambda: trigger_auto_bids_on_new_bid_task.delay(instance.auction.id))
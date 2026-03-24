from django.apps import AppConfig


class BidsConfig(AppConfig):
    name = 'bids'
    
    def ready(self):
        import bids.signals

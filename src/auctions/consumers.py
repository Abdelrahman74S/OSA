import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from auctions.models import AuctionListing
from bids.models import Bid
from django.db import transaction

class AuctionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.auction_id = self.scope["url_route"]["kwargs"]["auction_id"]
        self.room_group_name = f"auction_{self.auction_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        bid_amount = data.get("amount")
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.send(text_data=json.dumps({"error": "You must be logged in first"}))
            return

        result = await self.place_bid(user, bid_amount)
        
        if "error" in result:
            await self.send(text_data=json.dumps(result))
        else:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "auction_update",
                    "amount": str(result["amount"]),
                    "user": user.username,
                }
            )

    async def auction_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_bid",
            "amount": event["amount"],
            "user": event["user"]
        }))

    @database_sync_to_async
    def place_bid(self, user, amount):
        try:
            with transaction.atomic():
                auction = AuctionListing.objects.select_for_update().get(id=self.auction_id)
                try:
                    amount = float(amount)
                except (TypeError, ValueError):
                    return {"error": "Invalid bid amount"}
        
                current = auction.current_price if auction.current_price is not None else auction.starting_price
                if amount <= current:
                    return {"error": "Bid must be higher than the current price"}
        
                Bid.objects.create(auction=auction, bidder=user, amount=amount)
                auction.current_price = amount
                auction.save()
            return {"amount": amount}
    
        except AuctionListing.DoesNotExist:
            return {"error": "Auction does not exist"}
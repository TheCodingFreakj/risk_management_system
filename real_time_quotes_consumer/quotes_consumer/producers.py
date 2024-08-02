# consumers.py

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger('quotes_consumer.consumers')

class QuoteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("quotes", self.channel_name)
        await self.accept()
        logger.debug(f"WebSocket connection established: {self.channel_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("quotes", self.channel_name)
        logger.debug(f"WebSocket connection closed: {self.channel_name}")

    async def receive(self, text_data):
        logger.debug(f"Received message: {text_data}")

    async def send_quote(self, event):
        quote = event['quote']
        await self.send(text_data=json.dumps({'quote': quote}))
        logger.debug(f"Sent quote to WebSocket client: {quote}")


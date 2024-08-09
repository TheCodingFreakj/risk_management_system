import asyncio
import threading
from .fetch_realtime_data import  manage_connections
from ...start_consume import start_consumer_with_retries
from django.core.management.base import BaseCommand
from ...loggin_config import logger

class Command(BaseCommand):
    help = 'Run Kafka consumer'
    
    def handle(self, *args, **kwargs):
        start_consumer_with_retries()
        asyncio.run(manage_connections(['AAPL', 'GOOG', 'TSLA']))
        # start_consumer_with_retries()
        # List of stock symbols



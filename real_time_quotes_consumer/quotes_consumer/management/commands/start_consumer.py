import asyncio
import threading

from ...start_consume import start_consumer_with_retries
from .fetch_realtime_data import  check_market_calendar, fetch_extended_hours_data, fetch_historical_data, fetch_snapshot_data, manage_connections
# from ...start_consume import start_consumer_with_retries
from django.core.management.base import BaseCommand
from ...loggin_config import logger
# import alpaca_trade_api as tradeapi
class Command(BaseCommand):
    help = 'Run Kafka consumer'
    
    def handle(self, *args, **kwargs):
        start_consumer_with_retries()
        # symbols = ['AAPL', 'GOOG', 'TSLA', 'MSFT', 'AMZN']
        # fetch_historical_data(symbols)
        # fetch_snapshot_data(symbols)
        # fetch_extended_hours_data(symbols)
        # check_market_calendar()
        # asyncio.run(manage_connections(['AAPL', 'GOOG', 'TSLA']))
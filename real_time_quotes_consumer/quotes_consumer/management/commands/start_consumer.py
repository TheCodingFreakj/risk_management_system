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
        symbols = ['AAPL', 'GOOG', 'TSLA', 'MSFT', 'AMZN']
        fetch_historical_data(symbols)
        fetch_snapshot_data(symbols)
        fetch_extended_hours_data(symbols)
        check_market_calendar()
        # asyncio.run(manage_connections(['AAPL', 'GOOG', 'TSLA']))
        # for symbol in symbols:
        #     try:
        #         # Get the snapshot of the asset's current market data
        #         snapshot = api.get_snapshot(symbol)
                
        #         # Accessing latest trade and quote data
        #         latest_trade = snapshot.latest_trade
        #         latest_quote = snapshot.latest_quote
                
        #         print(f"Symbol: {symbol}")
        #         print(f"Last Trade Price: {latest_trade.price}")
        #         print(f"Last Quote Bid: {latest_quote.bid_price}")
        #         print(f"Last Quote Ask: {latest_quote.ask_price}")
        #         print("-------------------------------------------------")
                
        #     except tradeapi.rest.APIError as e:
        #         print(f"Error fetching data for {symbol}: {e}")
        #     except AttributeError as e:
        #         print(f"Attribute error for symbol {symbol}: {e}")
        # start_consumer_with_retries()
        # asyncio.run(manage_connections(['AAPL', 'GOOG', 'TSLA']))
        # start_consumer_with_retries()
        # List of stock symbols



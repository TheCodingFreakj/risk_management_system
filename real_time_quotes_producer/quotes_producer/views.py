from pathlib import Path
import requests
import os
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.conf import settings
from .kafka_producer import KafkaProducerPool  # Import the KafkaProducerPool
from dotenv import load_dotenv
import logging
import yfinance as yf
# Load environment variables from .env file
env_path = "../.env"
print(env_path)
load_dotenv(dotenv_path=env_path)

# Set up logging
logger = logging.getLogger(__name__)

class StockDataViewSet(viewsets.ViewSet):
    VANTAGE_API_KEY = os.getenv('VANTAGE_API_KEY', 'your_finnhub_api_key')
    SYMBOLS =  ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']  # Add more symbols as needed
    # USA_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA','HSBA.L', 'BARC.L', 'VOD.L', 'BP.L', 'RDSA.L']


    def get_stock_quote(self,symbol):
        data_for_kafka = {}
        stock = yf.Ticker(symbol)
        current_quote = stock.info
        logger.debug(f'Current quote for {symbol}:')
        relevant_fields = [
            'currentPrice', 'previousClose', 'open', 'dayHigh', 'dayLow',
            'volume', 'marketCap', 'dividendYield', 'peRatio', 'epsTrailingTwelveMonths'
        ]
        current_quote_filtered = {key: current_quote[key] for key in relevant_fields if key in current_quote}
        
        # Log the current quote as a dictionary
        logger.debug(f'Current quote for {symbol}: {current_quote_filtered}')  
        return current_quote_filtered    
                

    @action(detail=True, methods=['post'])
    def producetokafka(self, request):
        kafka_pool = KafkaProducerPool().initialize(pool_size=5, max_age_minutes=10, max_messages=1000)
        logger.debug(f"self.SYMBOLS--------------->{self.SYMBOLS}")
        logger.debug(f"self.SYMBOLS--------------->{self.SYMBOLS}")

        return self.send_messages_for_group(self.SYMBOLS, kafka_pool)
     
    def send_messages_for_group(self, symbols, kafka_pool):
        for symbol in symbols:
            data = self.get_stock_quote(symbol)
            logger.debug(f'Produced data to Kafka for {symbol}: {data}')
            if data:
                kafka_pool.send_message(settings.KAFKA_TOPIC, {"symbol": symbol, "data": data})
                logger.info(f'Produced data to Kafka for {symbol}: {data}')
            else:
                logger.error(f'No data to produce to Kafka for {symbol}') 
        return Response({"status": "Data produced to Kafka successfully"})           

        
        









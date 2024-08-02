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

# Load environment variables from .env file
env_path = "../.env"
print(env_path)
load_dotenv(dotenv_path=env_path)

# Set up logging
logger = logging.getLogger(__name__)

class StockDataViewSet(viewsets.ViewSet):
    FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', 'your_finnhub_api_key')
    SYMBOLS = ['AAPL', 'GOOGL', 'MSFT']  # Add more symbols as needed
    

    def get_stock_quote(self, symbol):
        url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.FINNHUB_API_KEY}'
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f'Failed to fetch data for {symbol}: {response.status_code}')
            return None

    @action(detail=True, methods=['post'])
    def producetokafka(self, request):
        kafka_pool = KafkaProducerPool().initialize()

        for symbol in self.SYMBOLS:
            data = self.get_stock_quote(symbol)
            logger.debug(f'Produced data to Kafka for {symbol}: {data}')
            if data:
                kafka_pool.send_message(settings.KAFKA_TOPIC, data)
                logger.info(f'Produced data to Kafka for {symbol}: {data}')
            else:
                logger.error(f'No data to produce to Kafka for {symbol}')
        
        return Response({"status": "Data produced to Kafka successfully"})









# const socket = new WebSocket('ws://localhost:8000/ws/quotes/');

# socket.onmessage = function(event) {
#     const data = JSON.parse(event.data);
#     console.log('Received:', data);
# };
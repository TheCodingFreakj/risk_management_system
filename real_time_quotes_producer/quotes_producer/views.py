from datetime import date, timedelta
from pathlib import Path
from django.http import JsonResponse
import requests
import os
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.conf import settings
from django.db.models import Avg, Max, Min
from .models import DailyReturn, PortfolioReturn, VaR
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

    def get_stock_quote(self, symbol):
        data_for_kafka = {}
        stock = yf.Ticker(symbol)

        # Fetch the latest historical data to get the latest date
        historical_data = stock.history(period="1d")  # Fetch data for today
        latest_date = historical_data.index[-1] if not historical_data.empty else None

        # Get the current stock quote
        current_quote = stock.info
        logger.debug(f'Current quote for {symbol}:')

        # Define the relevant fields to filter
        relevant_fields = [
            'currentPrice', 'previousClose', 'open', 'dayHigh', 'dayLow',
            'volume', 'marketCap', 'dividendYield', 'trailingPE', 'trailingEps'
        ]

        # Filter the current quote to include only relevant fields
        current_quote_filtered = {key: current_quote.get(key, None) for key in relevant_fields}

        # Add the latest date to the filtered quote
        if latest_date:
            current_quote_filtered['latestDate'] = latest_date.strftime('%Y-%m-%d')

        # Log the current quote as a dictionary with the latest date
        logger.debug(f'Current quote for {symbol}: {current_quote_filtered}')
        
        return current_quote_filtered
    # def get_stock_quote(self,symbol):
    #     data_for_kafka = {}
    #     stock = yf.Ticker(symbol)
    #     current_quote = stock.info
    #     logger.debug(f'Current quote for {symbol}:')
    #     relevant_fields = [
    #         'currentPrice', 'previousClose', 'open', 'dayHigh', 'dayLow',
    #         'volume', 'marketCap', 'dividendYield', 'peRatio', 'epsTrailingTwelveMonths'
    #     ]
    #     current_quote_filtered = {key: current_quote[key] for key in relevant_fields if key in current_quote}
        
    #     # Log the current quote as a dictionary
    #     logger.debug(f'Current quote for {symbol}: {current_quote_filtered}')  
    #     return current_quote_filtered    
                

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


    # View to retrieve and display daily returns for a specific ticker
def daily_returns_view(request, ticker):
    # Retrieve the daily returns for the given ticker
    daily_returns = DailyReturn.objects.filter(ticker=ticker).order_by('date')
    
    # Prepare data for display
    data = {
        'ticker': ticker,
        'returns': list(daily_returns.values('date', 'return_value'))
    }
    
    return JsonResponse(data)

# View to retrieve and display portfolio returns over a date range
def portfolio_returns_view(request):
    # Optionally, get the date range from query parameters
    start_date = request.GET.get('start_date', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', date.today().strftime('%Y-%m-%d'))
    
    # Retrieve the portfolio returns within the specified date range
    portfolio_returns = PortfolioReturn.objects.filter(date__range=[start_date, end_date]).order_by('date')
    
    # Calculate average, max, and min returns (example aggregate data)
    avg_return = portfolio_returns.aggregate(Avg('return_value'))['return_value__avg']
    max_return = portfolio_returns.aggregate(Max('return_value'))['return_value__max']
    min_return = portfolio_returns.aggregate(Min('return_value'))['return_value__min']
    
    # Prepare data for display
    data = {
        'start_date': start_date,
        'end_date': end_date,
        'returns': list(portfolio_returns.values('date', 'return_value')),
        'avg_return': avg_return,
        'max_return': max_return,
        'min_return': min_return
    }
    
    return JsonResponse(data)

# View to retrieve and display the latest Value-at-Risk (VaR)
def var_view(request):
    # Retrieve the most recent VaR entry
    latest_var = VaR.objects.latest('date')
    
    # Prepare data for display
    data = {
        'date': latest_var.date,
        'var_value': latest_var.var_value,
        'confidence_level': latest_var.confidence_level
    }
    
    return JsonResponse(data)         






    
    









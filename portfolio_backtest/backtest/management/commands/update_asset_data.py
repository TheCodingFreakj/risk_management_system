# backtest/management/commands/update_asset_data.py

from django.core.management.base import BaseCommand
import requests
from backtest.models import Asset
import yfinance as yf

class Command(BaseCommand):
    help = 'Update asset data from an external API'

    def handle(self, *args, **kwargs):
        symbols = {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corp.',
            'GOOGL': 'Google',
            'AMZN': 'Amazon',
            'TSLA': 'Tesla',
            'JNJ': 'Johnson & Johnson',
            'PG': 'Procter & Gamble Co.'
        }
        API_KEY = 'cqjbehpr01qnjotffkq0cqjbehpr01qnjotffkqg'
        for symbol,name  in symbols.items():
            response = requests.get(f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}')
            data = response.json()
            market_cap = self.get_market_cap(symbol, data['c'])
            volatility = self.calculate_volatility(symbol)
            asset, created = Asset.objects.update_or_create(
                symbol=symbol,
                defaults={
                    'name': name,
                    'market_cap': market_cap,
                    'volatility': volatility,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created new asset: {symbol}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated asset: {symbol}"))

                
    def get_market_cap(self, symbol, current_price):
        # Example calculation of market cap, requires shares outstanding
        shares_outstanding = self.fetch_shares_outstanding(symbol)
        return int(current_price * shares_outstanding)

    def calculate_volatility(self, symbol):
        # Example: Fetch historical data and calculate volatility
        historical_prices = self.fetch_historical_prices(symbol)
        return self.compute_volatility(historical_prices)

    def fetch_shares_outstanding(self, symbol):
        stock = yf.Ticker(symbol)
        shares_outstanding = stock.info.get('sharesOutstanding')
        
        if shares_outstanding is not None:
            return int(shares_outstanding)
        else:
            raise ValueError("Shares outstanding data not found")
            
           

    def fetch_historical_prices(self, symbol):
        # Fetch historical data using yfinance
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1y")  # Fetch 1 year of historical data
        
        # Extract the closing prices
        closing_prices = hist['Close'].tolist()
        print(f"fetch_historical_prices---------------> {closing_prices}")
        
        return closing_prices

    def compute_volatility(self, prices):
        # Calculate the standard deviation of daily returns
        import numpy as np
        returns = np.diff(prices) / prices[:-1]
        return np.std(returns)        

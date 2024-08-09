# charts/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
import alpaca_trade_api as tradeapi
from .serializers import StockDataSerializer
from datetime import date
class StockDataAPIView(APIView):
    def get(self, request, format=None):
        API_KEY = 'PKGE0HW03AZIO2Z1MXDA'
        API_SECRET = 'Py5Rg5CNfQKWqiVt5HIzbSBkQSQ8d8leepYyFfJh'
        BASE_URL = 'https://paper-api.alpaca.markets'  # Use 'https://api.alpaca.markets' for live trading

        api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

        # Define the array of stock symbols and fetch the initial data
        stock_symbols = ['AAPL', 'GOOGL', 'MSFT']  # Add more symbols as needed
        start_date = '2023-01-01'
        end_date = date.today()

        all_data = []

        for symbol in stock_symbols:
            # Fetch historical data for each symbol
            symbol_data = api.get_bars(symbol, tradeapi.TimeFrame.Day, start=start_date, end=end_date,feed='iex').df
            symbol_data.reset_index(inplace=True)
            print(symbol_data)
            symbol_data['symbol'] = symbol  # Add a column for the symbol
            all_data.append(symbol_data)

        # Combine data for all symbols
        combined_data = pd.concat(all_data)

        # Convert the data to JSON format using the serializer
        serializer = StockDataSerializer(combined_data.to_dict(orient='records'), many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

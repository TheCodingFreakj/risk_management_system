import requests
from .loggin_config import logger
import yfinance as yf


def fetch_historical_data(symbols, api_key):

    for symbol in symbols:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # logger.debug(f"The historic data -----------------> {symbol}")
            # store this database
            return data  # Closing prices

        else:
            print(f"Failed to fetch data: {response.status_code}")
            return None


def fetch_historic_data(symbols):
    for symbol in symbols:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1y")
        data['symbol'] = symbol
        return data



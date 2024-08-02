import requests


def fetch_historical_data(symbol, api_key):
    url = f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution=D&count=50&token={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        #store this database
        return data['c']  # Closing prices
    
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return None
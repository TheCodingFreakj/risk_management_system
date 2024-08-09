from django.http import JsonResponse
from django.shortcuts import render
import plotly.graph_objects as go
import pandas as pd
import redis
import json
import threading
import asyncio
import queue
import logging
import aiohttp
from django.conf import settings
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import plotly.io as pio

# Configure Redis connection
redis_client = redis.Redis(host='redis', port=6379, db=0)

logger = logging.getLogger(__name__)

async def fetch_stock_data_from_api(response_queue):
    url = f'http://charts:8005/api/stock-data/'
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    stock_data = await response.json()
                    response_queue.put(stock_data)
                    logger.info(f"stock_data from response_queue: {response_queue}")
                else:
                    logger.error(f"Error: {response.status}")
                    response_queue.put(None)
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {e}")
            response_queue.put(None)

def run_fetch_stock_data_in_thread(response_queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(fetch_stock_data_from_api(response_queue))

def fetch_stock_data():
    response_queue = queue.Queue()
    thread = threading.Thread(target=run_fetch_stock_data_in_thread, args=(response_queue,))
    thread.start()
    thread.join()
    
    stock_data = response_queue.get()
    # logger.info(f"stock_data from fetch_stock_data: {stock_data}")
    return stock_data

def plot_graph(df, raw_data=[], symbol=None):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Candlestick'
    ))

    fig.update_layout(
        title=f"{symbol if len(raw_data) != 0 else df['symbol'].iloc[0]} Real-Time Stock Price",
        xaxis_title='Time',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False
    )

    combined_data = {symbol if len(raw_data) != 0 else df['symbol'].iloc[0]: fig.to_html(full_html=False)}
    return combined_data


def real_time_stock(raw_data, symbol):
    logger.info(f"Showing From redis cache")
    data = [json.loads(item) for item in raw_data]
    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df['time'])
    return plot_graph(df,raw_data, symbol)

def get_stock_data():
    logger.info(f"Fetching from external API...")
    stock_data = fetch_stock_data()
    if stock_data and all(isinstance(item, dict) for item in stock_data):
        chart_html = {}
        df = pd.DataFrame(stock_data)
        df['time'] = pd.to_datetime(df['timestamp'])
        
        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol]
            chart_html.update(plot_graph(symbol_df, symbol=symbol))
        
        return chart_html
   



def chart_data(request):
    chart_html = {}
    symbols = ['AAPL', 'GOOG', 'TSLA']
    for symbol in symbols:
        logger.info(f"Checking symbol: {symbol}")
        raw_data = redis_client.lrange(symbol, 0, 5)
        logger.info(f"Checking raw_data for {symbol}: {raw_data}")
        if raw_data:
            chart_html[symbol] = real_time_stock(raw_data, symbol)
            logger.info(f"Updated chart_html with {symbol} data: {chart_html[symbol]}")
        else:
            break

    if not chart_html:
        chart_html = get_stock_data()
    return JsonResponse(chart_html)
def retrieve_risk_management_data():
    base_url = "http://realtimequotesproducer:8003/quotes_producer/"
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    urls = []
    for ticker in tickers:
        ticker_urls = {
            "daily_returns": f"{base_url}daily-returns/{ticker}/",
            "portfolio_returns": f"{base_url}portfolio-returns/",
            "var": f"{base_url}var/"
        }
        urls.append(ticker_urls)
    logger.info(f"Checking ticker_urls {ticker_urls}")
    all_ticker_data = {}
    for ticker_urls in urls:
        ticker = ticker_urls["daily_returns"].split("/")[-2]  # Extract ticker from URL
        all_ticker_data[ticker] = fetch_ticker_data(ticker_urls)  
    
    return all_ticker_data   


def fetch_api_data(url, params=None):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return None
# Function to handle fetching data for a specific ticker
def fetch_ticker_data(ticker_urls):
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_url = {executor.submit(fetch_api_data, url): key for key, url in ticker_urls.items()}
        
        for future in as_completed(future_to_url):
            key = future_to_url[future]
            try:
                data = future.result()
                results[key] = data
            except Exception as exc:
                print(f"{ticker_urls[key]} generated an exception: {exc}")
    
    return results

   


def index(request):
    all_ticker_data = retrieve_risk_management_data()
    
    graphs = {}

    for ticker, data in all_ticker_data.items():
        logger.info(f"Checking data for ticker: {ticker}")
        
        if data:  # Check if the data is not None
            # Access daily returns data
            daily_returns_data = data.get("daily_returns", {}).get("returns", [])
            portfolio_returns_data = data.get("portfolio_returns", {}).get("returns", [])
            var_data = data.get("var", {})
            
            # Generate Daily Returns Plotly Graph
            daily_returns_fig = go.Figure()
            daily_returns_fig.add_trace(go.Scatter(
                x=[entry['date'] for entry in daily_returns_data],
                y=[entry['return_value'] for entry in daily_returns_data],
                mode='lines',
                name=f'{ticker} Daily Returns'
            ))
            daily_returns_fig.update_layout(
                title=f'Daily Returns for {ticker}',
                xaxis_title='Date',
                yaxis_title='Return'
            )
            
            # Convert the Plotly figure to HTML div string
            daily_returns_div = pio.to_html(daily_returns_fig, full_html=False)

            # Generate Portfolio Returns Plotly Graph
            portfolio_returns_fig = go.Figure()
            portfolio_returns_fig.add_trace(go.Scatter(
                x=[entry['date'] for entry in portfolio_returns_data],
                y=[entry['return_value'] for entry in portfolio_returns_data],
                mode='lines',
                name=f'{ticker} Portfolio Returns'
            ))
            portfolio_returns_fig.update_layout(
                title=f'Portfolio Returns for {ticker}',
                xaxis_title='Date',
                yaxis_title='Return'
            )

            # Convert the Plotly figure to HTML div string
            portfolio_returns_div = pio.to_html(portfolio_returns_fig, full_html=False)

            # Store the graphs in the dictionary
            graphs[ticker] = {
                'daily_returns_div': daily_returns_div,
                'portfolio_returns_div': portfolio_returns_div,
                'var_value': var_data.get('var_value'),
                'confidence_level': var_data.get('confidence_level'),
            }

        logger.info(f"Ticker: {ticker}, Daily Returns: {len(daily_returns_data)}, Portfolio Returns: {len(portfolio_returns_data)}")
    
    # Pass the graphs dictionary to the template after processing all tickers
    context = {
        'graphs': graphs
    }
    
    return render(request, 'quotes_consumer/index.html', context)



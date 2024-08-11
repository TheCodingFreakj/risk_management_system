import math
from django.http import JsonResponse
from django.shortcuts import render
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import redis
import json
import threading
import asyncio
import queue
import logging
import yfinance as yf
from datetime import datetime, timedelta
import aiohttp
from django.conf import settings
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import plotly.io as pio
from django.db import connection
from datetime import datetime
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
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
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
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
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

def make_decision(daily_returns, portfolio_returns, var_value, market_returns_dict, threshold_var_percentage=2.0):
    # Calculate portfolio volatility
    portfolio_volatility = np.std(daily_returns)
    
    # Calculate market volatilities for each index in the dictionary
    market_volatilities = {index: np.std(returns) for index, returns in market_returns_dict.items()}
    
    # Use the average or maximum market volatility as a threshold (example: maximum)
    max_market_volatility = max(market_volatilities.values())
    some_volatility_threshold = max_market_volatility * 1.1  # Example threshold: 10% higher than the highest market volatility
    
    # Evaluate recent performance based on the last 5 days
    recent_performance = np.mean(portfolio_returns[-5:])  # Last 5 days average return
    
    # Assess VaR Value
    var_value_percentage = abs(var_value) * 100
    high_risk = var_value_percentage > threshold_var_percentage
    
    # Decision-Making Logic
    if high_risk and portfolio_volatility > some_volatility_threshold and recent_performance < 0:
        decision = (
            "The portfolio is currently experiencing high volatility relative to the market and negative performance over the last 5 days. "
            "Given the elevated risk and recent downturn, it is advisable to reduce exposure "
            "to high-risk assets to protect the portfolio from further potential losses."
        )
    elif not high_risk and recent_performance > 0:
        decision = (
            "The portfolio is showing positive performance over the last 5 days with manageable risk levels. "
            "Consider maintaining or even increasing exposure to capitalize on the upward trend, "
            "while still keeping an eye on market conditions."
        )
    else:
        decision = (
            "The portfolio's performance over the last 5 days is uncertain, with a mix of volatility and varying returns. "
            "Monitor the situation closely and be prepared to adjust your strategy as needed. "
            "Stay informed about market developments that could impact your portfolio."
        )
    
    return decision  

def market_returns():
    # Define the market indices tickers
    indices = {
        'NASDAQ Composite': '^IXIC',
        'Russell 2000': '^RUT',
        'FTSE 100': '^FTSE',
        'Nikkei 225': '^N225',
        'S&P 500': '^GSPC'
    }

    # Initialize a dictionary to hold the market returns as NumPy arrays
    market_returns_np = {}

    # Loop through each index and fetch the data
    for name, ticker in indices.items():
        # Download the adjusted close price for the last year including up to today
        data = yf.download(ticker, period='1mo')['Adj Close']

        # Calculate the market returns as the percentage change
        returns = data.pct_change().dropna()
        
        # Convert the returns Series to a NumPy array and store it in the dictionary
        market_returns_np[name] = returns.to_numpy()

    return market_returns_np



def make_short_term_decision(price_data, rsi, macd, signal_line, moving_average, volatility_threshold=0.02, ma_short=50, ma_long=200):
    volatility = np.std(price_data)
    current_price = price_data.iloc[-1]  # Get the most recent price
    macd_value = macd.iloc[-1] if isinstance(macd, pd.Series) else macd  # Handle MACD as Series or scalar
    signal_line_value = signal_line.iloc[-1] if isinstance(signal_line, pd.Series) else signal_line  # Handle Signal Line as Series or scalar
    moving_avg_value = moving_average  # Assume moving_average is already a scalar
    rsi_value = rsi.iloc[-1] if isinstance(rsi, pd.Series) else rsi  # Handle RSI as Series or scalar
    ma_crossover = ma_short - ma_long  # Assuming you provide scalar values for ma_short and ma_long

    # Example of conditions using scalar values
    if rsi_value > 80 and macd_value > signal_line_value and current_price > moving_avg_value and volatility < volatility_threshold:
        return "Strong Buy; market is showing strong upward momentum with low volatility."
    
    elif rsi_value > 70 and macd_value > 0 and current_price > moving_avg_value and volatility < volatility_threshold:
        return "Buy; indicators suggest upward momentum, but be cautious of potential overbought conditions."
    
    elif rsi_value > 50 and macd_value > signal_line_value and ma_crossover > 0:
        return "Buy on dips; market is in a bullish trend but consider waiting for a slight pullback."
    
    elif rsi_value < 20 and macd_value < signal_line_value and current_price < moving_avg_value and volatility < volatility_threshold:
        return "Strong Sell; market is showing strong downward momentum with low volatility."
    
    elif rsi_value < 30 and macd_value < 0 and current_price < moving_avg_value and volatility < volatility_threshold:
        return "Sell; indicators suggest downward momentum, but be cautious of potential oversold conditions."
    
    elif rsi_value < 50 and macd_value < signal_line_value and ma_crossover < 0:
        return "Sell on rallies; market is in a bearish trend but consider waiting for a slight upward correction."
    
    elif volatility >= volatility_threshold:
        return "Avoid trading; high volatility indicates uncertain market conditions."
    
    elif ma_crossover > 0 and current_price > moving_avg_value:
        return "Hold; bullish trend confirmed, but no immediate action recommended."
    
    elif ma_crossover < 0 and current_price < moving_avg_value:
        return "Hold; bearish trend confirmed, but no immediate action recommended."
    
    else:
        return "Hold; no strong signals detected, wait for clearer market conditions."


API_KEY_V='BJ9RB5D8OE9UX05M'

API_KEY='cqjbehpr01qnjotffkq0cqjbehpr01qnjotffkqg'

def fetch_financial_data_finnhub(ticker):
    base_url = 'https://finnhub.io/api/v1'

    # Fetch financials reported data
    financials_url = f'{base_url}/stock/financials-reported?symbol={ticker}&token={API_KEY}'
    financials_response = requests.get(financials_url)
    financials_data = financials_response.json()

    # Initialize variables for financial metrics
    total_equity = None
    total_liabilities = None
    net_income = None
    total_revenue = None
    gross_profit=None
    operating_income = None


    # Extract the most recent financial report data
    if 'data' in financials_data:
        year = financials_data["data"][0]["year"]
        report = financials_data['data'][0]['report']  # Get the report from the first item in data
        
        # Parse the balance sheet (bs)
        if 'bs' in report:
            for item in report['bs']:
                concept = item.get('concept')
                value = item.get('value')
                if concept == 'us-gaap_StockholdersEquity':
                    total_equity = value
                elif concept == 'us-gaap_Liabilities':
                    total_liabilities = value
        
        # Parse the income statement (ic)
        if 'ic' in report:
            for item in report['ic']:
                concept = item.get('concept')
                value = item.get('value')
                if concept == 'us-gaap_NetIncomeLoss':
                    net_income = value
                elif concept == 'us-gaap_SalesRevenueNet':
                    total_revenue = value
                elif concept == 'us-gaap_GrossProfit':
                    gross_profit = value
                elif concept == 'us-gaap_OperatingIncomeLoss':
                    operating_income = value
             
    financial_data = {
        'total_equity': total_equity,
        'total_liabilities': total_liabilities,
        'net_income': net_income,
        'total_revenue': total_revenue,
        'gross_profit': gross_profit,
        'operating_income': operating_income
    }
    


    return financial_data
    

    
  
def get_market_growth(symbol='SPY'):
    # Fetch historical market data for the specified symbol using yfinance
    df = yf.download(symbol, period='5y', interval='1mo')
    # Print all the keys (columns) of the DataFrame
    print("DataFrame columns:", df.columns)

    if not df.empty:
        # Calculate Market Growth for each year
        df['Year'] = df.index.year
        df['Close'] = df['Adj Close']  # Use Adjusted Close for accurate growth calculations
        df = df.groupby('Year')['Close'].agg(['first', 'last'])
        df['Market_Growth'] = df['last'] / df['first'] - 1
        df = df[['Market_Growth']].reset_index()
        
        return df
    else:
        print("Error fetching data from yfinance")
        return None
def calculate_financial_ratios(financial_data):
    # Calculate Debt-to-Equity Ratio
    debt_to_equity = None
    if financial_data['total_liabilities'] is not None and financial_data['total_equity'] is not None:
        if financial_data['total_equity'] != 0:
            debt_to_equity = financial_data['total_liabilities'] / financial_data['total_equity']
    
    # Calculate Return on Equity (ROE)
    roe = None
    if financial_data['total_equity'] is not None and financial_data['total_equity'] != 0:
        if financial_data['net_income'] is not None:
            roe = financial_data['net_income'] / financial_data['total_equity']

    # Calculate Gross Margin
    gross_margin = None
    if financial_data['total_revenue'] is not None and financial_data['total_revenue'] != 0:
        if financial_data['gross_profit'] is not None:
            gross_margin = financial_data['gross_profit'] / financial_data['total_revenue']

    return {
        'debt_to_equity': debt_to_equity,
        'roe': roe,
        'gross_margin': gross_margin
    }

def evaluate_investment(ticker, financial_data, financial_ratios, thresholds):
    decision = {
        'action': 'Hold',  # Default action
        'reasons': []
    }

    # Evaluate Debt-to-Equity Ratio
    if financial_ratios['debt_to_equity'] is not None and financial_ratios['debt_to_equity'] > thresholds['max_debt_to_equity']:
        decision['reasons'].append(f"High Debt-to-Equity Ratio: {financial_ratios['debt_to_equity']:.2f}")

    # Evaluate ROE
    if financial_ratios['roe'] is not None:
        if financial_ratios['roe'] < thresholds['min_roe']:
            decision['reasons'].append(f"Low ROE: {financial_ratios['roe']:.2%}")
    else:
        decision['reasons'].append("ROE data not available")
    
    # Evaluate Gross Margin
    if financial_ratios['gross_margin'] is not None:
        if financial_ratios['gross_margin'] < thresholds['min_gross_margin']:
            decision['reasons'].append(f"Low Gross Margin: {financial_ratios['gross_margin']:.2%}")
    
    # Final Decision
    if len(decision['reasons']) == 0:
        decision['action'] = "Buy"
    elif len(decision['reasons']) > 2:
        decision['action'] = "Sell"
    else:
        decision['action'] = "Hold"
    
    # Construct the decision string
    reasons_str = " ".join(decision['reasons']) if decision['reasons'] else "Meets all criteria."
    decision_string = f"Investment Decision for {ticker}: {decision['action']}. Reasons: {reasons_str}"
    
    return decision_string






def calculate_macd(price_data, short_window=12, long_window=26, signal_window=9):
    # Calculate the short-term EMA (12 periods by default)
    short_ema = price_data.ewm(span=short_window, adjust=False).mean()
    
    # Calculate the long-term EMA (26 periods by default)
    long_ema = price_data.ewm(span=long_window, adjust=False).mean()
    
    # Calculate the MACD (difference between short-term EMA and long-term EMA)
    macd = short_ema - long_ema
    
    # Calculate the Signal Line (9-period EMA of the MACD)
    signal_line = macd.ewm(span=signal_window, adjust=False).mean()
    
    return macd, signal_line
def analyze_group_of_symbols(symbols):
    results = {}
    market_growth_symbol = 'SPY'
    market_growth = get_market_growth(symbol=market_growth_symbol)

    if market_growth is not None:
        avg_market_growth = market_growth['Market_Growth'].mean()
        print(f"Average Market Growth: {avg_market_growth:.2f}")
    else:
        print("Market growth analysis failed.")
        return
    
    thresholds = {
        'max_debt_to_equity': 2.0,
        'min_roe': 0.15,
        'min_gross_margin': 0.40
    }

    if avg_market_growth < 1.0:
        thresholds['min_roe'] += 0.05
        thresholds['min_gross_margin'] += 0.05
    elif avg_market_growth > 1.1:
        thresholds['min_roe'] -= 0.05
        thresholds['min_gross_margin'] -= 0.05

    for symbol in symbols:
        financial_data = fetch_financial_data_finnhub(symbol)
        financial_ratios = calculate_financial_ratios(financial_data)
        
        long_term_decision = evaluate_investment(symbol, financial_data, financial_ratios, thresholds)

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
        price_data = yf.download(symbol, start=start_date, end=end_date)['Adj Close']

        macd, signal_line = calculate_macd(price_data)
        moving_average = np.mean(price_data)
        rsi = 75  # Example RSI value
        
        short_term_decision = make_short_term_decision(price_data, rsi, macd, signal_line, moving_average)
        
        results[symbol] = {
            'short_term_decision': short_term_decision,
            'long_term_decision': long_term_decision,
            'price_data': price_data,
            'rsi': rsi,
            'macd': macd,
            'moving_average': moving_average,
            'financial_data': financial_data
        }
    
    return results

# Function to create Plotly graphs for short-term analysis and return HTML
def plot_short_term_analysis_html(symbol, data):
    price_data = data['price_data']
    rsi = data['rsi']
    macd = data['macd']
    moving_average = data['moving_average']

    # Create price plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(price_data))), y=price_data, mode='lines', name='Price'))
    fig.add_trace(go.Scatter(x=list(range(len(price_data))), y=[moving_average]*len(price_data),
                             mode='lines', name='Moving Average', line=dict(dash='dash', color='orange')))

    fig.update_layout(title=f"Short-Term Analysis for {symbol}",
                      xaxis_title="Time",
                      yaxis_title="Price")

    # Create RSI and MACD plot
    fig.add_trace(go.Scatter(x=list(range(len(price_data))), y=[rsi]*len(price_data),
                             mode='lines', name='RSI', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=list(range(len(price_data))), y=[macd]*len(price_data),
                             mode='lines', name='MACD', line=dict(color='red')))

    # Convert plot to HTML
    return pio.to_html(fig, full_html=False)

# Function to create Plotly graphs for long-term analysis and return HTML
def plot_long_term_analysis_html(symbol, financial_data):
    labels = list(financial_data.keys())
    values = [financial_data[label] for label in labels]

    fig = go.Figure([go.Bar(x=labels, y=values, text=values, textposition='auto')])

    fig.update_layout(title=f"Long-Term Analysis for {symbol}",
                      xaxis_title="Financial Metrics",
                      yaxis_title="Values")

    # Convert plot to HTML
    return pio.to_html(fig, full_html=False)

def generate_summary(symbol, decisions):
    short_term_decision = decisions['short_term_decision']
    long_term_decision = decisions['long_term_decision']
    
    # Start the summary
    summary = f"For {symbol}, the analysis suggests the following actions:\n\n"
    
    # Short-term summary
    summary += f"In the short-term, it is recommended to {short_term_decision.lower()}.\n"
    
    # Long-term summary
    summary += f"In the long-term, the strategy should focus on {long_term_decision.lower()}.\n"
    
    # Additional context or considerations
    summary += "These recommendations are based on the latest market trends and financial data. "
    summary += "Please consider the overall market conditions and your investment strategy before making any decisions."
    
    return summary
def get_decision_html(decision_results):
    html_output = """
    <style>
        .grid-container {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr; /* Three equal-width columns */
            grid-gap: 20px; /* Spacing between grid items */
            margin: 20px 0; /* Margin above and below the grid */
        }

        .grid-item {
            padding: 10px;
            border: 1px solid #ccc; /* Border around each grid item */
            border-radius: 5px; /* Rounded corners */
            background-color: #f9f9f9; /* Background color for grid items */
        }

        .grid-item h2 {
            margin-top: 0; /* Remove top margin for h2 in grid items */
        }
    </style>
    """

    # Initialize an array to hold HTML entries for all symbols
    entries = []

    # Example loop through multiple symbols and their decisions
    for symbol, decisions in decision_results.items():
        summary = generate_summary(symbol, decisions)
        entry_html = '<div class="grid-container">'

        # Short-term decision and plot
        entry_html += f"""
        <div class="grid-item">
            <h2>Decisions for {symbol} - Short-term</h2>
            <p><strong>Decision:</strong> {decisions['short_term_decision']}</p>
            {plot_short_term_analysis_html(symbol, decisions)}
        </div>
        """

        # Long-term decision and plot
        entry_html += f"""
        <div class="grid-item">
            <h2>Decisions for {symbol} - Long-term</h2>
            <p><strong>Decision:</strong> {decisions['long_term_decision']}</p>
            {plot_long_term_analysis_html(symbol, decisions['financial_data'])}
        </div>
        """

        # Add a third item (e.g., additional information, analysis, or summary)
        entry_html += f"""
            <div class="grid-item">
                <h2>Additional Analysis for {symbol}</h2>
                <p><strong>Summary:</strong> {summary}</p>
            </div>
            """

        entry_html += '</div><hr>'  # Close the grid container and add a horizontal rule

        # Add the generated HTML to the entries array
        entries.append(entry_html)

    # Concatenate all entries to form the final HTML output
    html_output += ''.join(entries)


    return html_output

def index(request):
    """

    This is for third component which show long term and short term decision making
    on UI

    """ 
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

    logger.debug(f"DECISION----------------------------------------> {analyze_group_of_symbols(symbols)}")
    
    # Analyze group of symbols for short-term and long-term decisions
    decision_results = analyze_group_of_symbols(symbols)

    
    
    # Get HTML output
    html_output = get_decision_html(decision_results)

    """
    This is for second component which shows general decision making
    on UI
    """ 
    all_ticker_data = retrieve_risk_management_data()
    market_returns_dict=market_returns()
    
    graphs = {}

    for ticker, data in all_ticker_data.items():
        # logger.info(f"Checking data for ticker: {ticker}")
        
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
                                    # Extracting the return values into a list
            daily_returns = [item['return_value'] for item in daily_returns_data]

            # Converting the list to a NumPy array
            daily_returns = np.array(daily_returns)

            # Assuming the portfolio_returns as a subset, for example, the last 7 days' returns
            portfolio_returns = [item['return_value'] for item in portfolio_returns_data]
                        # Converting the list to a NumPy array
            portfolio_returns = np.array(portfolio_returns)
            #logger.info(f"Ticker: {ticker} Daily Returns: {len(daily_returns_data)}, Portfolio Returns: {len(portfolio_returns_data)}")
                    # Make the decision
            decision = make_decision(daily_returns, portfolio_returns, var_data.get('var_value'),market_returns_dict)
            #logger.info(f"Ticker: {ticker}, decision {decision}")
            # Store the graphs in the dictionary
            graphs[ticker] = {
                'daily_returns_div': daily_returns_div,
                'portfolio_returns_div': portfolio_returns_div,
                'var_value': round((var_data.get('var_value')), 2),
                'percentage': round((abs(var_data.get('var_value')) * 100), 2),
                'confidence_level': var_data.get('confidence_level')* 100,
                'decision': decision
            }


    """

    This is for first component which shows stress testing 
    on UI

    """ 
    raw_query = "SELECT * FROM stress_scenario"

    # Execute the raw SQL query
    with connection.cursor() as cursor:
        cursor.execute(raw_query)
        rows = cursor.fetchall()
    scenarios = []

    for row in rows:
        scenario = {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'impact_factor': row[3]
        }
        scenarios.append(scenario)
     # Pass the graphs dictionary to the template after processing all tickers
    context = {
        'graphs': graphs,
        'scenarios':scenarios,
        'html_output':html_output
    }

    logger.info(f"scenarios----------------------------> {scenarios}")
    
    return render(request, 'quotes_consumer/index.html', context)

def get_scenario_data(request, scenario_id):
    # Use raw SQL to fetch the scenario data
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name, description, impact_factor FROM stress_scenario WHERE id = %s", [scenario_id])
        scenario = cursor.fetchone()

    # If the scenario is not found, return a 404 response
    if scenario is None:
        return JsonResponse({'error': 'Scenario not found'}, status=404)

    # Unpack the scenario data
    scenario_id, name, description, impact_factor = scenario

    # Simulate the portfolio value changes under this scenario
    portfolio_value = 1000000  # Assume initial portfolio value is 1,000,000
    impact_values = [portfolio_value * (1 + impact_factor * i) for i in range(1, 6)]

    # Example of categories or labels (e.g., different sectors or assets)
    categories = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    categories2 = ['Technology', 'Healthcare', 'Energy', 'Finance', 'Consumer Goods']
    categories3=['Equities', 'Bonds', 'Real Estate', 'Commodities', 'Cash']
    categories4 = ['North America', 'Europe', 'Asia', 'Latin America', 'Africa']

    # Generate a bar chart for each category
    charts = []

    for cat, title in zip([categories, categories2, categories3, categories4], 
                          ["Stocks", "Sectors", "Asset Types", "Geographical Regions"]):
        bar_chart = go.Bar(x=cat, y=impact_values)
        layout = go.Layout(
            title=f'Impact of {name} on Portfolio Value - {title}',
            xaxis={'title': title},
            yaxis={'title': 'Portfolio Value'},
            width=700,
            height=300,
        )
        fig = go.Figure(data=[bar_chart], layout=layout)
        charts.append(fig.to_json())

    # Combine all chart JSONs into a single response
    response_data = {
        "chart1": charts[0],
        "chart2": charts[1],
        "chart3": charts[2],
        "chart4": charts[3],
    }

    return JsonResponse(response_data, safe=False)

import datetime
import json
import asyncio
import websockets
from dateutil.parser import isoparse
import redis
from django.core.management.base import BaseCommand
from ...loggin_config import logger
import alpaca_trade_api as tradeapi
API_KEY = 'PKGE0HW03AZIO2Z1MXDA'
API_SECRET = 'Py5Rg5CNfQKWqiVt5HIzbSBkQSQ8d8leepYyFfJh'
BASE_URL = 'https://paper-api.alpaca.markets'
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')
# Configure Redis connection
redis_client = redis.Redis(host='redis', port=6379, db=0)

# async def fetch_stock_data(symbol):
#     logger.debug(f"Starting fetch_stock_data for {symbol}")
#     source = "iex"
#     uri = f"wss://stream.data.alpaca.markets/v2/{source}"
#     backoff = 1  # Start with a 1-second backoff

#     while True:
#         try:
#             async with websockets.connect(uri) as websocket:
#                 # Authenticate
#                 auth_payload = {
#                     "action": "auth",
#                     "key": API_KEY,
#                     "secret": API_SECRET
#                 }
#                 logger.debug(f"Sending auth payload: {auth_payload}")
#                 await websocket.send(json.dumps(auth_payload))
#                 auth_response = await websocket.recv()
#                 logger.debug(f"Auth response: {auth_response}")

#                 try:
#                     auth_data = json.loads(auth_response)
#                     logger.debug(f"Parsed auth data: {auth_data}")

#                     if isinstance(auth_data, list):
#                         for message in auth_data:
#                             if message.get('msg') == 'connected':
#                                 logger.debug("Authorization successful")
#                             else:
#                                 logger.error(f"Authorization failed: {auth_data}")
#                                 return
#                     elif isinstance(auth_data, dict) and auth_data.get('status') != 'authorized':
#                         logger.error(f"Authorization failed: {auth_data}")
#                         return

#                 except json.JSONDecodeError as e:
#                     logger.error(f"JSON decode error: {e}")
#                     return

#                 # Subscribe
#                 subscribe_payload = {
#                     "action": "subscribe",
#                     "trades": symbol
#                 }
#                 logger.debug(f"Sending subscribe payload: {subscribe_payload}")
#                 await websocket.send(json.dumps(subscribe_payload))
#                 subscribe_response = await websocket.recv()
#                 logger.debug(f"Subscribe response: {subscribe_response}")

#                 # Reset backoff on successful connection
#                 backoff = 1

#                 # Log subscription confirmation separately
#                 subscribe_data = json.loads(subscribe_response)
#                 if isinstance(subscribe_data, list):
#                     for sub in subscribe_data:
#                         if sub.get('T') == 'subscription':
#                             logger.debug(f"Subscription confirmation: {sub}")
#                             break

#                 # Listen for messages
#                 while True:
#                     try:
#                         message = await websocket.recv()
#                         logger.debug(f"Received message: {message}")
#                         data = json.loads(message)
#                         logger.debug(f"Parsed message data: {data}")

#                         if isinstance(data, list):
#                             for trade in data:
#                                 logger.debug(f"Processing trade data: {trade}")
#                                 if trade.get('T') == 'subscription':
#                                     logger.debug(f"Subscription confirmation: {trade}")
#                                 elif trade.get('T') == 't':  # Handling trade messages
#                                     time = isoparse(trade['t'])
#                                     price = trade['p']
#                                     trade_data = {'time': time.isoformat(), 'price': price}

#                                     redis_client.lpush(symbol, json.dumps(trade_data))
#                                     redis_client.ltrim(symbol, 0, 5)
#                                     logger.debug(f"Updated Redis for {symbol}: {redis_client.lrange(symbol, 0, 5)}")
#                                 elif trade.get('T') == 'c':  # Handling correction messages
#                                     correction_data = {
#                                         'original_id': trade['id'],
#                                         'time': isoparse(trade['t']).isoformat(),
#                                         'price': trade['p'],
#                                         'size': trade['s'],
#                                         'correction_type': trade['x']
#                                     }
#                                     redis_client.lpush(f"{symbol}_corrections", json.dumps(correction_data))
#                                     redis_client.ltrim(f"{symbol}_corrections", 0, 5)
#                                     logger.debug(f"Updated Redis for {symbol} corrections: {redis_client.lrange(f'{symbol}_corrections', 0, 5)}")
#                         elif isinstance(data, dict) and data.get('T') == 'subscription':
#                             logger.debug(f"Subscription confirmation: {data}")
#                         else:
#                             logger.debug(f"Unexpected data format: {data}")
#                     except websockets.ConnectionClosedError as e:
#                         logger.error(f"Connection closed with error {e.code}: {e.reason}")
#                         break
#                     except Exception as e:
#                         logger.error(f"Error receiving message: {e}")
#                         break
#         except Exception as e:
#             logger.error(f"Failed to connect: {e}")
#             await asyncio.sleep(backoff)
#             backoff = min(backoff * 2, 60)  # Exponential backoff with a maximum of 60 seconds
async def fetch_stock_data(symbols):
    uri = "wss://stream.data.alpaca.markets/v2/iex"

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                # Step 1: Authenticate
                auth_payload = {
                    "action": "auth",
                    "key": API_KEY,
                    "secret": API_SECRET
                }
                logger.debug(f"Sending auth payload: {json.dumps(auth_payload)}")
                await websocket.send(json.dumps(auth_payload))
                
                # Receive and check authentication response
                auth_response = await websocket.recv()
                logger.debug(f"Auth response: {auth_response}")
                auth_data = json.loads(auth_response)
                if auth_data[0].get("T") == "error":
                    logger.error(f"Authentication error: {auth_data[0]['msg']}")
                    return

                logger.debug("Authorization successful")

                # Step 2: Subscribe to symbols
                subscribe_payload = {
                    "action": "subscribe",
                    "trades": symbols
                }
                logger.debug(f"Sending subscribe payload: {json.dumps(subscribe_payload)}")
                await websocket.send(json.dumps(subscribe_payload))
                
                # Receive and check subscription response
                subscribe_response = await websocket.recv()
                logger.debug(f"Subscribe response: {subscribe_response}")
                
                # Step 3: Listen for trade messages
                while True:
                    try:
                        message = await websocket.recv()
                        logger.debug(f"Received message: {message}")
                        data = json.loads(message)

                        if isinstance(data, list):
                            for item in data:
                                if item['T'] == 't':  # Trade message
                                    logger.info(f"Trade update: {item}")
                                    # Process trade data (e.g., store, display, trigger actions)
                                elif item['T'] == 'c':  # Correction message
                                    logger.info(f"Correction update: {item}")
                                    # Handle correction data
                                elif item['T'] == 'cancelError':  # Cancellation error
                                    logger.info(f"Cancellation error: {item}")
                                    # Handle cancellation error
                        else:
                            logger.warning(f"Received unexpected data format: {data}")

                    except websockets.ConnectionClosedError as e:
                        logger.error(f"Connection closed: {e}")
                        break
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        break

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            await asyncio.sleep(5)  # Backoff before retrying

async def run_fetch_stock_data(symbol):
    try:
        logger.debug(f"Fetching data for {symbol}")
        await fetch_stock_data(symbol)
        logger.debug(f"Completed fetching data for {symbol}")
    except Exception as e:
        logger.error(f"Error fetching data: {e}")

async def manage_connections(symbol):

    await run_fetch_stock_data(symbol)
    await asyncio.sleep(1)  # Small delay to prevent immediate reconnection

# Function to store data in Redis
def store_in_redis(key, value):
    redis_client.set(key, json.dumps(value))
    print(f"Stored data in Redis with key: {key}")

# Function to fetch and store historical data
def fetch_historical_data(symbols):
    print("\nFetching Historical Data...")
    timeframe = '1Min'
    for symbol in symbols:
        try:
            # Fetch the historical data as a DataFrame
            bars_df = api.get_bars(symbol, timeframe, limit=5,feed='iex').df
            data = []
            
            # Iterate over each row in the DataFrame
            for index, bar in bars_df.iterrows():
                data.append({
                    "time": index.isoformat(),  # Use the index as the time
                    "open": bar['open'],
                    "high": bar['high'],
                    "low": bar['low'],
                    "close": bar['close'],
                    "volume": bar['volume']
                })
            
            # Store the data in Redis
            store_in_redis(f"historical:{symbol}", data)
            print(f"Historical data for {symbol} stored in Redis.")
        except tradeapi.rest.APIError as e:
            print(f"Error fetching historical data for {symbol}: {e}")

# Function to fetch and store snapshot data
def fetch_snapshot_data(symbols):
    print("\nFetching Snapshot Data...")
    for symbol in symbols:
        try:
            snapshot = api.get_snapshot(symbol)
            data = {
                "latest_trade": {
                    "price": snapshot.latest_trade.price if snapshot.latest_trade else None
                },
                "latest_quote": {
                    "bid_price": snapshot.latest_quote.bid_price if snapshot.latest_quote else None,
                    "ask_price": snapshot.latest_quote.ask_price if snapshot.latest_quote else None
                }
            }
            store_in_redis(symbol, data)
            print(f"Snapshot data for {symbol} stored in Redis.")
        except tradeapi.rest.APIError as e:
            print(f"Error fetching snapshot data for {symbol}: {e}")
# Function to calculate dynamic times
def calculate_time_range():
    now = datetime.datetime.now(datetime.timezone.utc)  # Current UTC time
    
    # Determine if it's after-hours or pre-market based on current time
    market_close_time = now.replace(hour=20, minute=0, second=0, microsecond=0)
    market_open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
    
    if now.time() > datetime.time(16, 0) and now.time() <= datetime.time(20, 0):
        # After-Hours: 4:00 PM to 8:00 PM ET
        start_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
        end_time = market_close_time
    elif now.time() < datetime.time(9, 30):
        # Pre-Market: 4:00 AM to 9:30 AM ET
        start_time = now.replace(hour=4, minute=0, second=0, microsecond=0)
        end_time = market_open_time
    else:
        # Default to regular market hours (9:30 AM to 4:00 PM ET)
        start_time = market_open_time
        end_time = now  # Current time

    return start_time.isoformat(), end_time.isoformat()
# Function to fetch and store pre-market and after-hours data

def fetch_extended_hours_data(symbols):
    print("\nFetching Pre-Market and After-Hours Data...")
    start_time, end_time = calculate_time_range()
    
    for symbol in symbols:
        try:
            # Fetch the historical data as a DataFrame
            bars_df = api.get_bars(symbol, '1Min', start=start_time, end=end_time,feed='iex').df
            data = []
            
            # Iterate over each row in the DataFrame
            for index, bar in bars_df.iterrows():
                data.append({
                    "time": index.isoformat(),  # Use the index as the time
                    "open": bar['open'],
                    "high": bar['high'],
                    "low": bar['low'],
                    "close": bar['close'],
                    "volume": bar['volume']
                })
            
            # Store the data in Redis
            store_in_redis(f"extended_hours:{symbol}", data)
            print(f"Extended hours data for {symbol} stored in Redis.")
        except tradeapi.rest.APIError as e:
            print(f"Error fetching extended hours data for {symbol}: {e}")

# Function to check and store the market calendar
def check_market_calendar():
    print("\nChecking Market Calendar...")
    today = datetime.date.today().isoformat()
    calendar = api.get_calendar(start=today, end=today)
    for day in calendar:
        data = {
            "date": day.date.isoformat(),
            "open": day.open.isoformat(),
            "close": day.close.isoformat()
        }
        store_in_redis(f"market_calendar:{day.date.isoformat()}", data)
        print(f"Market calendar for {day.date.isoformat()} stored in Redis.")

import json
import asyncio
import websockets
from dateutil.parser import isoparse
import redis
from django.core.management.base import BaseCommand
from ...loggin_config import logger

API_KEY = 'PKGE0HW03AZIO2Z1MXDA'
API_SECRET = 'Py5Rg5CNfQKWqiVt5HIzbSBkQSQ8d8leepYyFfJh'


# Configure Redis connection
redis_client = redis.Redis(host='redis', port=6379, db=0)

async def fetch_stock_data(symbol):
    logger.debug(f"Starting fetch_stock_data for {symbol}")
    source = "iex"
    uri = f"wss://stream.data.alpaca.markets/v2/{source}"
    backoff = 1  # Start with a 1-second backoff

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                # Authenticate
                auth_payload = {
                    "action": "auth",
                    "key": API_KEY,
                    "secret": API_SECRET
                }
                logger.debug(f"Sending auth payload: {auth_payload}")
                await websocket.send(json.dumps(auth_payload))
                auth_response = await websocket.recv()
                logger.debug(f"Auth response: {auth_response}")

                try:
                    auth_data = json.loads(auth_response)
                    logger.debug(f"Parsed auth data: {auth_data}")

                    if isinstance(auth_data, list):
                        for message in auth_data:
                            if message.get('msg') == 'connected':
                                logger.debug("Authorization successful")
                            else:
                                logger.error(f"Authorization failed: {auth_data}")
                                return
                    elif isinstance(auth_data, dict) and auth_data.get('status') != 'authorized':
                        logger.error(f"Authorization failed: {auth_data}")
                        return

                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    return

                # Subscribe
                subscribe_payload = {
                    "action": "subscribe",
                    "trades": [symbol]
                }
                logger.debug(f"Sending subscribe payload: {subscribe_payload}")
                await websocket.send(json.dumps(subscribe_payload))
                subscribe_response = await websocket.recv()
                logger.debug(f"Subscribe response: {subscribe_response}")

                # Reset backoff on successful connection
                backoff = 1

                # Log subscription confirmation separately
                subscribe_data = json.loads(subscribe_response)
                if isinstance(subscribe_data, list):
                    for sub in subscribe_data:
                        if sub.get('T') == 'subscription':
                            logger.debug(f"Subscription confirmation: {sub}")
                            break

                # Listen for messages
                while True:
                    try:
                        message = await websocket.recv()
                        logger.debug(f"Received message: {message}")
                        data = json.loads(message)
                        logger.debug(f"Parsed message data: {data}")

                        if isinstance(data, list):
                            for trade in data:
                                logger.debug(f"Processing trade data: {trade}")
                                if trade.get('T') == 'subscription':
                                    logger.debug(f"Subscription confirmation: {trade}")
                                elif trade.get('T') == 't':  # Handling trade messages
                                    time = isoparse(trade['t'])
                                    price = trade['p']
                                    trade_data = {'time': time.isoformat(), 'price': price}

                                    redis_client.lpush(symbol, json.dumps(trade_data))
                                    redis_client.ltrim(symbol, 0, 5)
                                    logger.debug(f"Updated Redis for {symbol}: {redis_client.lrange(symbol, 0, 5)}")
                                elif trade.get('T') == 'c':  # Handling correction messages
                                    correction_data = {
                                        'original_id': trade['id'],
                                        'time': isoparse(trade['t']).isoformat(),
                                        'price': trade['p'],
                                        'size': trade['s'],
                                        'correction_type': trade['x']
                                    }
                                    redis_client.lpush(f"{symbol}_corrections", json.dumps(correction_data))
                                    redis_client.ltrim(f"{symbol}_corrections", 0, 5)
                                    logger.debug(f"Updated Redis for {symbol} corrections: {redis_client.lrange(f'{symbol}_corrections', 0, 5)}")
                        elif isinstance(data, dict) and data.get('T') == 'subscription':
                            logger.debug(f"Subscription confirmation: {data}")
                        else:
                            logger.debug(f"Unexpected data format: {data}")
                    except websockets.ConnectionClosedError as e:
                        logger.error(f"Connection closed with error {e.code}: {e.reason}")
                        break
                    except Exception as e:
                        logger.error(f"Error receiving message: {e}")
                        break
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)  # Exponential backoff with a maximum of 60 seconds

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



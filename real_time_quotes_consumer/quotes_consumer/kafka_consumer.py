from kafka import KafkaConsumer, KafkaAdminClient, TopicPartition
from kafka.admin import ConfigResource, ConfigResourceType
from django.conf import settings
import ssl
import json

import pandas as pd

from .models import StockPrice
from .loggin_config import logger
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time
from datetime import datetime, timedelta

class KafkaConsumerService:
    def __init__(self, topic, timeout_seconds=20, fetch_delay_seconds=2):
        self.topic = topic
        context = ssl.create_default_context()
        context.load_verify_locations(settings.KAFKA_CA_CERT)
        context.load_cert_chain(certfile=settings.KAFKA_CLIENT_CERT, keyfile=settings.KAFKA_CLIENT_KEY)

        self.consumer = KafkaConsumer(
            enable_auto_commit=False,  # Disable auto commit
            bootstrap_servers=settings.KAFKA_BROKER_URLS,
            client_id="Real_Time_Quotes_Aggregate",
            group_id="Real_Time_Quotes_Aggregate_GROUP",
            auto_offset_reset="latest",  # Start from the latest message
            security_protocol="SSL",
            ssl_context=context,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self.partition = TopicPartition(topic, 0)  # Assuming partition 0
        self.consumer.assign([self.partition])
        self.start_time = time.time()
        self.timeout_seconds = timeout_seconds
        self.fetch_delay_seconds = fetch_delay_seconds
        self.cached_messages = []
        self.message_processed = False
    def calculate_signal(self,message,current_price):

        historical_data_df=self.compareWithCurrentPrice(message)
                # Check if the DataFrame is empty
        if historical_data_df.empty:
            logger.warning(f"No historical data found for symbol: {message}. Skipping processing.")
            return
        
        # logger.debug(f"historical_data_df: {historical_data_df}")
        # Assuming message["data"]["currentPrice"] should be a dictionary
        current_price_data = int(current_price)
        if isinstance(current_price_data, tuple):
            current_price_data = dict(current_price_data)  # Convert to dictionary if it's a tuple

        # Create a DataFrame for the current price
        current_price_df = pd.DataFrame([current_price_data])
                # Check if the current_price_df is empty
        if current_price_df.empty:
            logger.warning("Current price data is empty. Skipping processing.")
            return
        # Concatenate the historical data with the current price
        current_data = pd.concat([historical_data_df, current_price_df], ignore_index=True)
                    # Recalculate indicators with the current price
        current_data['SMA_20'] = current_data['close_price'].rolling(window=20).mean()
        current_data['SMA_50'] = current_data['close_price'].rolling(window=50).mean()
        current_data['RSI_14'] = self.calculate_rsi(current_data, 14)
        current_data['EMA_12'] = current_data['close_price'].ewm(span=12, adjust=False).mean()
        current_data['EMA_26'] = current_data['close_price'].ewm(span=26, adjust=False).mean()
        current_data['MACD'] = current_data['EMA_12'] - current_data['EMA_26']
        current_data['Signal_Line'] = current_data['MACD'].ewm(span=9, adjust=False).mean()
        signal = self.generate_signal(current_data)
        return signal
         
            
    def consume_messages(self):
        while True:
            current_time = time.time()
            logger.info(f"Starting to consume messages using SSL----> {current_time - self.start_time}")
            
            # Re-seek to the latest 5 minutes messages if timeout occurs
            if current_time - self.start_time >= self.timeout_seconds:
                self.seek_to_latest_five_minutes()
                self.start_time = current_time
            new_messages = []
            logger.info(f"Starting to consume messages using SSL---> {self.message_processed}")   
            for message in self.consumer:
                message_timestamp = datetime.fromtimestamp(message.timestamp / 1000)  # Convert milliseconds to seconds
                if self.is_last_five_minutes(message_timestamp):
                    logger.info(f"Processing Message------->: {message}")
                    logger.info(f"Processing message_timestamp------->: {message_timestamp}")
                  
                    # signal = self.calculate_signal(message.value['symbol'],message.value["data"]["currentPrice"] )
                    self.process_message(message.value, message.value['symbol'], message.value["data"]["currentPrice"] )
                    new_messages.append((message.value, datetime.now()))  # Add message with reception time
                    self.consumer.commit()
                    logger.info(f"Commiting Messages------->{new_messages}")
                    self.message_processed = True
                    logger.info(f"Updating Messages and inserting to cache------->")
                    self.update_cache(new_messages)
                time.sleep(5)
                logger.info(f"Not last minute message------->{self.is_last_five_minutes(message_timestamp)}")
                break

            logger.info(f"Coming out of the self.consumer loop------->")
            if self.message_processed == True and self.cached_messages:
                # Process cached messages if no new message was processed
                logger.info("No new messages received. Reprocessing cached messages.")
                for cached_message, _ in self.cached_messages:
                    # signal = self.calculate_signal(cached_message['symbol'],cached_message["data"]["currentPrice"] )
                    self.process_message(cached_message, cached_message['symbol'], cached_message["data"]["currentPrice"])
                self.message_processed = False    
   




    def update_cache(self, new_messages):
        """
        Update the cache with the latest 5 minutes of messages.
        """
        current_time = datetime.now()
        five_minutes_ago = current_time - timedelta(minutes=5)
        
        # Add new messages to the cache
        self.cached_messages.extend(new_messages)
        
        # Filter the cache to keep only messages from the last 5 minutes
        self.cached_messages = [
            (msg, timestamp) for msg, timestamp in self.cached_messages
            if timestamp >= five_minutes_ago
        ]     
    def is_last_five_minutes(self, message_timestamp):
        """
        Check if the message timestamp is within the last five minutes.
        """
        current_time = datetime.now()
        five_minutes_ago = current_time - timedelta(minutes=5)
        return message_timestamp >= five_minutes_ago
    

        # Calculate RSI
    def calculate_rsi(self, data, window):
        data['close_price'] = data['close_price'].astype(float)
        delta = data['close_price'].diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def compareWithCurrentPrice(self,symbol):

        historical_data = StockPrice.objects.filter(symbol=symbol).all()
                # Check if the QuerySet is empty
        if not historical_data.exists():
            logger.warning(f"No historical data found for symbol: {symbol}")
            return pd.DataFrame() 
        # logger.debug(f"historical_data: {historical_data}")
        # Convert the ORM query result to a DataFrame
        historical_data_df = pd.DataFrame([{
            'date': record.date,
            'open_price': record.open_price,
            'high_price': record.high_price,
            'low_price': record.low_price,
            'close_price': record.close_price,
            'volume': record.volume
        } for record in historical_data])
        # logger.debug(f"historical_data_df: {historical_data_df}")
                # Convert the date column to datetime format
        historical_data_df['date'] = pd.to_datetime(historical_data_df['date'])

        # Sort data by date
        historical_data_df = historical_data_df.sort_values(by='date')

        # Optionally, set the date as the index
        historical_data_df.set_index('date', inplace=True)


                # Calculate Moving Averages
        historical_data_df['SMA_20'] = historical_data_df['close_price'].rolling(window=20).mean()
        historical_data_df['SMA_50'] = historical_data_df['close_price'].rolling(window=50).mean()


        historical_data_df['RSI_14'] = self.calculate_rsi(historical_data_df, 14)

        # Calculate MACD
        historical_data_df['EMA_12'] = historical_data_df['close_price'].ewm(span=12, adjust=False).mean()
        historical_data_df['EMA_26'] = historical_data_df['close_price'].ewm(span=26, adjust=False).mean()
        historical_data_df['MACD'] = historical_data_df['EMA_12'] - historical_data_df['EMA_26']
        historical_data_df['Signal_Line'] = historical_data_df['MACD'].ewm(span=9, adjust=False).mean()
        # logger.debug(f"historical_data_df: {historical_data_df}")
        return historical_data_df
    
        # Define a simple moving average crossover strategy
    def generate_signal(self, current_data):
        # Get the last row of the DataFrame for the most recent indicators
        last_row = current_data.iloc[-1]

        # Log all relevant indicators for debugging
        # logger.debug(f"Latest Indicators for Signal Generation: {last_row[['SMA_20', 'SMA_50', 'RSI_14', 'MACD', 'Signal_Line']]}")

        # Example signal generation logic based on SMA, RSI, and MACD
        if last_row['SMA_20'] > last_row['SMA_50']:
            if last_row['RSI_14'] < 30 and last_row['MACD'] > last_row['Signal_Line']:
                logger.debug("Buy signal generated: SMA_20 > SMA_50, RSI < 30, MACD > Signal Line")
                return "buy"
            elif last_row['RSI_14'] > 70 and last_row['MACD'] < last_row['Signal_Line']:
                logger.debug("Sell signal generated: SMA_20 > SMA_50, RSI > 70, MACD < Signal Line")
                return "sell"
        elif last_row['SMA_20'] < last_row['SMA_50']:
            if last_row['RSI_14'] < 30 and last_row['MACD'] > last_row['Signal_Line']:
                logger.debug("Buy signal generated: SMA_20 < SMA_50, RSI < 30, MACD > Signal Line")
                return "buy"
            elif last_row['RSI_14'] > 70 and last_row['MACD'] < last_row['Signal_Line']:
                logger.debug("Sell signal generated: SMA_20 < SMA_50, RSI > 70, MACD < Signal Line")
                return "sell"

        # Additional condition for EMA crossovers (Optional)
        if last_row['EMA_12'] > last_row['EMA_26']:
            logger.debug("Buy signal generated: EMA_12 > EMA_26")
            return "buy"
        elif last_row['EMA_12'] < last_row['EMA_26']:
            logger.debug("Sell signal generated: EMA_12 < EMA_26")
            return "sell"

        # If none of the conditions are met, hold the position
        logger.debug("Hold signal generated: No conditions met for buy or sell")
        return "hold"
    def process_message(self, message, symbol, currentPrice):
        logger.debug(f"Processing Message--------------->: {message}")
        
        try:

            signal = self.calculate_signal(symbol,currentPrice)
            logger.debug(f"Processing Message--------------->: {signal}")
            message["signal"] = signal
           
            
            logger.info(f"Starting to consume messages using SSL---> {self.message_processed}")   



             # Get the channel layer
            channel_layer = get_channel_layer()
            logger.debug(f"Channel Layer: {channel_layer}")

            # Send message to the WebSocket group
            async_to_sync(channel_layer.group_send)(
                'quotes',
                {
                    'type': 'send_quote',
                    'quote': message
                }
            )
            logger.debug(f"Message sent to WebSocket: {message}")
            time.sleep(5)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    def seek_to_latest_five_minutes(self):
        """
        Seek to the offset corresponding to five minutes ago.
        """
        five_minutes_ago = int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000)
        offsets = self.consumer.offsets_for_times({self.partition: five_minutes_ago})
        offset = offsets[self.partition].offset if offsets[self.partition] else 0
        try:
            self.consumer.seek(self.partition, offset)
            logger.info(f"Offset reset to {offset} for partition: {self.partition.partition} on topic: {self.partition.topic}")
        except Exception as e:
            logger.error(f"Error resetting offset: {e}")


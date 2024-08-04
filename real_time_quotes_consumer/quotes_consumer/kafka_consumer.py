from kafka import KafkaConsumer, KafkaAdminClient, TopicPartition
from kafka.admin import ConfigResource, ConfigResourceType
from django.conf import settings
import ssl
import json
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
                    self.process_message(message.value)
                    new_messages.append((message.value, datetime.now()))  # Add message with reception time
                    self.consumer.commit()
                    logger.info(f"Commiting Messages------->{new_messages}")
                    self.message_processed = True
                    logger.info(f"Updating Messages and inserting to cache------->")
                    self.update_cache(new_messages)
                time.sleep(5)
                logger.info(f"Not last minute message------->")
                break

            logger.info(f"Coming out of the self.consumer loop------->")
            if self.message_processed == True and self.cached_messages:
                # Process cached messages if no new message was processed
                logger.info("No new messages received. Reprocessing cached messages.")
                for cached_message, _ in self.cached_messages:
                    self.process_message(cached_message)
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
    
    def process_message(self, message):
        logger.debug(f"Processing Message: {message}")
        try:
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
            logger.info(f"Starting to consume messages using SSL---> {self.message_processed}")   
          
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

    # def set_retention_policy(self, retention_ms=3600000):
    #     """
    #     Set the retention policy for the Kafka topic to delete messages older than the specified time.
    #     """
    #     try:
    #         admin_client = KafkaAdminClient(
    #             bootstrap_servers=settings.KAFKA_BROKER_URLS,
    #             client_id='retention_policy_client'
    #         )
            
    #         config_resource = ConfigResource(ConfigResourceType.TOPIC, self.topic)
    #         configs = {'retention.ms': retention_ms}

    #         admin_client.alter_configs({config_resource: configs})
    #         logger.info(f"Retention policy set for topic {self.topic}.")
    #     except Exception as e:
    #         logger.error(f"Failed to set retention policy: {e}")

from django.conf import settings
from kafka.errors import NoBrokersAvailable
from .loggin_config import logger
import time
def start_consumer_with_retries():
    max_retries = 5
    backoff_factor = 2
    attempt = 0

    while attempt < max_retries:
        try:
            from .kafka_consumer import KafkaConsumerService
            consumer = KafkaConsumerService(settings.KAFKA_TOPIC)
            # consumer.reset_offset(offset=100)
            consumer.consume_messages()
            break
        except NoBrokersAvailable as e:
            attempt += 1
            logger.error(f"No brokers available on attempt {attempt}: {e}")
            if attempt < max_retries:
                sleep_time = backoff_factor ** attempt
                logger.info(f"Retrying to start consumer in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error("Max retries reached. Failed to start consumer.")
                # Optional: Implement a fallback mechanism
                break
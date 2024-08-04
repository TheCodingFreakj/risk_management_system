import queue
import threading
from kafka import KafkaProducer
from django.conf import settings
import ssl
import json
from datetime import datetime, timedelta
from .loggin_config import logger
from kafka.errors import KafkaTimeoutError, KafkaError

class KafkaProducerWrapper:
    def __init__(self, producer):
        self.producer = producer
        self.creation_time = datetime.now()
        self.message_count = 0

    def increment_message_count(self):
        self.message_count += 1

    def needs_recycling(self, max_age_minutes=10, max_messages=1000):
        current_time = datetime.now()
        age = (current_time - self.creation_time).total_seconds() / 60
        return age > max_age_minutes or self.message_count > max_messages

    def close(self):
        self.producer.flush()
        self.producer.close()

class KafkaProducerPool:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(KafkaProducerPool, cls).__new__(cls)
        return cls._instance

    def initialize(self, pool_size=5, max_age_minutes=10, max_messages=1000):
        if not self._initialized:
            self.pool_size = pool_size
            self.max_age_minutes = max_age_minutes
            self.max_messages = max_messages
            self.pool = queue.Queue(maxsize=pool_size)
            self.lock = threading.Lock()
            self._initialize_pool()
            self._initialized = True
        return self

    def _initialize_pool(self):
        logger.debug("Initializing KafkaProducerPool")
        context = ssl.create_default_context()
        context.load_verify_locations(settings.KAFKA_CA_CERT)
        context.load_cert_chain(certfile=settings.KAFKA_CLIENT_CERT, keyfile=settings.KAFKA_CLIENT_KEY)

        for _ in range(self.pool_size):
            producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BROKER_URLS,
                security_protocol='SSL',
                ssl_context=context,
                value_serializer=lambda v: v if isinstance(v, bytes) else json.dumps(v).encode('utf-8'),
                acks='all',
                retries=5,
                request_timeout_ms=30000,
                retry_backoff_ms=500,
                linger_ms=10
            )
            wrapper = KafkaProducerWrapper(producer)
            self.pool.put(wrapper)
        logger.debug("KafkaProducerPool initialized")

    def get_producer(self):
        with self.lock:
            logger.debug("Getting a producer from the pool")
            wrapper = self.pool.get()
            logger.debug("Producer acquired")
            if wrapper.needs_recycling(self.max_age_minutes, self.max_messages):
                logger.debug("Recycling producer due to age or message count")
                wrapper.close()
                new_producer = self._create_new_producer()
                wrapper = KafkaProducerWrapper(new_producer)
            return wrapper

    def return_producer(self, wrapper):
        with self.lock:
            logger.debug("Returning a producer to the pool")
            self.pool.put(wrapper)
            logger.debug("Producer returned")

    def _create_new_producer(self):
        context = ssl.create_default_context()
        context.load_verify_locations(settings.KAFKA_CA_CERT)
        context.load_cert_chain(certfile=settings.KAFKA_CLIENT_CERT, keyfile=settings.KAFKA_CLIENT_KEY)

        new_producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BROKER_URLS,
            security_protocol='SSL',
            ssl_context=context,
            value_serializer=lambda v: v if isinstance(v, bytes) else json.dumps(v).encode('utf-8'),
            acks='all',
            retries=5,
            request_timeout_ms=30000,
            retry_backoff_ms=500,
            linger_ms=10
        )
        return new_producer

    def send_message(self, topic, value):
        if value:
            wrapper = self.get_producer()
            wrapper.increment_message_count()
            logger.debug(f"Producer trying to send message to topic {topic}, value: {value}")
            try:
                future = wrapper.producer.send(topic, value=value)
                result = future.get(timeout=10)
                logger.debug(f"Message sent to topic {topic}: {result}")
                wrapper.producer.flush()
            except KafkaTimeoutError as e:
                logger.error(f"KafkaTimeoutError: {e}")
                raise
            except KafkaError as e:
                logger.error(f"KafkaError: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to send message to Kafka: {e}")
                raise
            finally:
                self.return_producer(wrapper)
                logger.debug("Producer returned to the pool")

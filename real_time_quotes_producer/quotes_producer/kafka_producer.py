import queue
import threading
from kafka import KafkaProducer
from django.conf import settings
import ssl
import json
from .loggin_config import logger
from kafka.errors import KafkaTimeoutError
class KafkaProducerPool:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(KafkaProducerPool, cls).__new__(cls)
        return cls._instance

    def initialize(self, pool_size=5):
        if not self._initialized:
            self.pool_size = pool_size
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
            self.pool.put(producer)
        logger.debug("KafkaProducerPool initialized")

    def get_producer(self):
        with self.lock:
            logger.debug("Getting a producer from the pool")
            producer = self.pool.get()
            logger.debug("Producer acquired")
            return producer

    def return_producer(self, producer):
        with self.lock:
            logger.debug("Returning a producer to the pool")
            self.pool.put(producer)
            logger.debug("Producer returned")

    def send_message(self, topic, value):
        producer = self.get_producer()
        logger.debug(f"Producer trying to send message to topic {topic}, value: {value}")
        try:
            future = producer.send(topic, value=value)
            result = future.get(timeout=10)
            logger.debug(f"Message sent to topic {topic}: {result}")
        except KafkaTimeoutError as e:
            logger.error(f"KafkaTimeoutError: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {e}")
            raise
        finally:
            logger.debug("Returning a producer to the pool")
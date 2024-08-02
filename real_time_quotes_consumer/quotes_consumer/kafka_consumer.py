from kafka import KafkaConsumer
from django.conf import settings
import ssl
import json
from .loggin_config import logger
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
class KafkaConsumerService:
    def __init__(self, topic):
        context = ssl.create_default_context()
        context.load_verify_locations(settings.KAFKA_CA_CERT)
        context.load_cert_chain(certfile=settings.KAFKA_CLIENT_CERT, keyfile=settings.KAFKA_CLIENT_KEY)

        self.consumer = KafkaConsumer(
            topic,
            enable_auto_commit=False,  # Disable auto commit
            bootstrap_servers=settings.KAFKA_BROKER_URLS,
            client_id = "Real_Time_Quotes_Aggregate",
            group_id = "Real_Time_Quotes_Aggregate_GROUP",
            # sasl_mechanism = 'SCRAM-SHA-256',
            # sasl_plain_username=settings.KAFKA_USERNAME,
            # sasl_plain_password=settings.KAFKA_PASSWORD,
            security_protocol = "SSL",
            ssl_context=context,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
# .poll().values()
    def consume_messages(self):
        print("Printing message using SSL---------------------------------------------------> ")
        while True:
           for message in self.consumer:
              print(f"Got message using SSL--------------------------------------------------->  {message.value}")
        # for message in self.consumer:
              logger.debug(f"Received Message------->: {message.value}")
              self.process_message(message.value)
              self.consumer.commit()


    def process_message(self, message):
        logger.debug(f"Received Message------->: {message}")
        try:
            # Decode message if necessary (assuming message is a JSON string)
            # message_dict = json.loads(message)
            
            channel_layer = get_channel_layer()
            logger.debug(f"channel_layer------->: {channel_layer}")
            async_to_sync(channel_layer.group_send)(
                'quotes',
                {
                    'type': 'send_quote',
                    'quote': message  # Assuming message_dict is the structure you want to send
                }
            )

            logger.debug(f"message sent------->: {message}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message------->: {e}")
        except Exception as e:
            logger.error(f"Unexpected error------->: {e}")
                  

from ...start_consume import start_consumer_with_retries
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run Kafka consumer'

    def handle(self, *args, **kwargs):
        start_consumer_with_retries()
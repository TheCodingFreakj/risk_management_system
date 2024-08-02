from django.core.management.base import BaseCommand
from quotes_consumer.get_historic_data import fetch_historic_data

class Command(BaseCommand):
    help = 'Starts the scheduler.'

    def handle(self, *args, **kwargs):
        fetch_historic_data()
        self.stdout.write(self.style.SUCCESS('Scheduler started'))
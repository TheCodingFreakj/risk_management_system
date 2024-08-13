from django.core.management.base import BaseCommand
from quotes_producer.scheduler import start_scheduler

class Command(BaseCommand):
    help = 'Starts the scheduler.'

    def handle(self, *args, **kwargs):
        start_scheduler()
        self.stdout.write(self.style.SUCCESS('Scheduler is running...'))
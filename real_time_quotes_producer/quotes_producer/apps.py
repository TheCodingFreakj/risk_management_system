from threading import Thread
from django.apps import AppConfig
import os
import time
import requests
from django.core.management import call_command

class QuotesProducerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quotes_producer'


    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true':  # Ensure this runs only in the main process
            def start_scheduler_thread():
                time.sleep(10)  # Allow Django to fully start up
                from django.core.management import call_command
                call_command('runscheduler')

            # Start the scheduler in a new thread
            thread = Thread(target=start_scheduler_thread)
            thread.start()

  


    




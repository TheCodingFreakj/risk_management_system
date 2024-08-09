from django.apps import AppConfig
import os

class QuotesProducerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quotes_producer'

    def ready(self):

        #Only run scheduler when the development server starts
        if os.environ.get('RUN_MAIN') == 'true':
            from django.core.management import call_command
            call_command('runscheduler')



    




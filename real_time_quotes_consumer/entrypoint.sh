#!/bin/bash

# Start the Django server
daphne -b 0.0.0.0 -p 8002 real_time_quotes_consumer.asgi:application &

# # Start the Kafka consumer
python manage.py start_consumer

# python manage.py runscheduler

#!/bin/bash


# Start the Django development server
daphne -b 0.0.0.0 -p 8010 trading_platform.asgi:application



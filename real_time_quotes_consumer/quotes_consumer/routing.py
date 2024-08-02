

# routing.py

from django.urls import re_path
from . import producers

websocket_urlpatterns = [
    re_path(r'ws/quotes/$', producers.QuoteConsumer.as_asgi()),
]


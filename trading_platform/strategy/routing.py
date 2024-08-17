

# routing.py

from django.urls import re_path

from .consumers import BacktestConsumer


websocket_urlpatterns = [
    re_path(r'ws/backtest/$', BacktestConsumer.as_asgi()),
]


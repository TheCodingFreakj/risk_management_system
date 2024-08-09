# charts/serializers.py

from rest_framework import serializers

class StockDataSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    open = serializers.FloatField()
    high = serializers.FloatField()
    low = serializers.FloatField()
    close = serializers.FloatField()
    vwap = serializers.FloatField()
    volume = serializers.IntegerField()
    symbol = serializers.CharField()  # Add this line to include the stock symbol


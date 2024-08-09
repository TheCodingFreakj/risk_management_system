# charts/urls.py

from django.urls import path
from .views import StockDataAPIView

urlpatterns = [
    path('api/stock-data/', StockDataAPIView.as_view(), name='stock-data-api'),
]

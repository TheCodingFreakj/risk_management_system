from django.urls import path
from .views import StockDataViewSet

# Define the StockDataViewSet instance
stock_data_view = StockDataViewSet.as_view({
    'post': 'producetokafka'
})

urlpatterns = [
    path('stockdata/producetokafka/', stock_data_view, name='producetokafka'),
]

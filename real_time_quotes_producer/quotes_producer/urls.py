from django.urls import path
from .views import StockDataViewSet,daily_returns_view, portfolio_returns_view, var_view

# Define the StockDataViewSet instance
stock_data_view = StockDataViewSet.as_view({
    'post': 'producetokafka',
})

urlpatterns = [
    path('stockdata/producetokafka/', stock_data_view, name='producetokafka'),
    path('daily-returns/<str:ticker>/', daily_returns_view, name='daily_returns'),
    path('portfolio-returns/', portfolio_returns_view, name='portfolio_returns'),
    path('var/', var_view, name='var'),
]

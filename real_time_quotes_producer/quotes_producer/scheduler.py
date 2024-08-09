import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from django.db import transaction
from .models import DailyReturn, MarketData, PortfolioReturn, VaR
from .loggin_config import logger
import atexit
import yfinance as yf

scheduler = BackgroundScheduler()
@retry(stop=stop_after_attempt(5), wait=wait_fixed(10))  # Retry 5 times with a 10-second delay between attempts
def call_produce_to_kafka_viewset():
    try:
        response = requests.post('http://127.0.0.1:8003/quotes_producer/stockdata/producetokafka/')
        if response.status_code == 200:
            logger.info("Successfully called produce_to_kafka viewset.")
        else:
            logger.error(f'Failed to call produce_to_kafka viewset: {response.status_code}')
    except requests.RequestException as e:
        logger.exception("Exception occurred while calling produce_to_kafka viewset")
        raise e

@retry(stop=stop_after_attempt(5), wait=wait_fixed(10))
def fetch_store_historical_data():

    logger.info("This scheduler is running.")
    
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    data = yf.download(tickers, period='1y')['Adj Close']
    returns = data.pct_change().dropna()
    portfolio_returns = returns.mean(axis=1)
    confidence_level = 0.95
    var_value = np.percentile(portfolio_returns, (1 - confidence_level) * 100)
    
    market_data_list = []
    daily_return_list = []
    portfolio_return_list = []
    
    for ticker in tickers:
        for date, price in data[ticker].items():
            logger.info(f"This scheduler is running.-----------> {date}")
            if not MarketData.objects.filter(ticker=ticker, date=date).exists():
                market_data_list.append(MarketData(
                    ticker=ticker,
                    date=date,
                    price=price
                ))
        
        for date, return_value in returns[ticker].items():
            logger.info(f"This scheduler is running.-----------> {date}")
            if not DailyReturn.objects.filter(ticker=ticker, date=date).exists():
                daily_return_list.append(DailyReturn(
                    ticker=ticker,
                    date=date,
                    return_value=return_value
                ))
    
    for date, return_value in portfolio_returns.items():
        logger.info(f"This scheduler is running.-----------> {date}")
        if not PortfolioReturn.objects.filter(date=date).exists():
            portfolio_return_list.append(PortfolioReturn(
                date=date,
                return_value=return_value
            ))
    
    # Perform bulk insert in a single transaction
    with transaction.atomic():
        if market_data_list:
            MarketData.objects.bulk_create(market_data_list)
        
        if daily_return_list:
            DailyReturn.objects.bulk_create(daily_return_list)
        
        if portfolio_return_list:
            PortfolioReturn.objects.bulk_create(portfolio_return_list)
        
        # Store VaR (only one record, no need for bulk insert)
        last_date = portfolio_returns.index[-1]
        if not VaR.objects.filter(date=last_date).exists():
            logger.info(f"This scheduler is running.-----------> {last_date}")
            VaR.objects.update_or_create(
                date=last_date,
                defaults={'var_value': var_value, 'confidence_level': confidence_level}
            )          


def start_scheduler():

    if not scheduler.running:
        scheduler.start()
        trigger = DateTrigger(run_date=None)  # `None` means "now"
        scheduler.add_job(call_produce_to_kafka_viewset, trigger=trigger)
        #scheduler.add_job(fetch_store_historical_data, trigger=trigger)

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()

atexit.register(stop_scheduler)

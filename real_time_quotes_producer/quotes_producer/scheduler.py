from datetime import datetime
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
    
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    # Download the adjusted close price for the last year including up to today
    data = yf.download(tickers, period='5d', interval='1m')['Adj Close']

    # Ensure we get the most recent data up to today
    data = data.asfreq('B').ffill()  # 'B' frequency fills in business days
    returns = data.pct_change().dropna()
    # Calculate the number of tickers
    num_tickers = len(tickers)

        # Calculate equal weights dynamically
    weights = np.ones(num_tickers) / num_tickers

    # Calculate portfolio returns with dynamic weights
    portfolio_returns = returns.dot(weights)

    confidence_levels = [0.90, 0.95, 0.99]

   

    
    
    
    market_data_list = []
    daily_return_list = []
    portfolio_return_list = []
    
    for ticker in tickers:
        for date, price in data[ticker].items():
            
            if not MarketData.objects.filter(ticker=ticker, date=date).exists():
                logger.info(f"This MarketData scheduler is running.----------->{ticker} , {date}")
                market_data_list.append(MarketData(
                    ticker=ticker,
                    date=date,
                    price=price
                ))
        logger.info(f"This MarketData scheduler is skipping.----------->{ticker}, {date}")         
        
        for date, return_value in returns[ticker].items():
            
            if not DailyReturn.objects.filter(ticker=ticker, date=date).exists():
                logger.info(f"This DailyReturn scheduler is running.----------->{ticker}, {date}")
                daily_return_list.append(DailyReturn(
                    ticker=ticker,
                    date=date,
                    return_value=return_value
                ))
        logger.info(f"This DailyReturn scheduler is skipping.----------->{ticker}, {date}")    
    for date, return_value in portfolio_returns.items():
        
        if not PortfolioReturn.objects.filter(date=date).exists():
            logger.info(f"This PortfolioReturn scheduler is running.----------->{ticker}, {date}")
            portfolio_return_list.append(PortfolioReturn(
                date=date,
                return_value=return_value
            ))
        logger.info(f"This PortfolioReturn scheduler is skipping.----------->{ticker}, {date}")    
        # Bulk create the records in the database to optimize performance
    MarketData.objects.bulk_create(market_data_list)
    DailyReturn.objects.bulk_create(daily_return_list)
    PortfolioReturn.objects.bulk_create(portfolio_return_list)
    last_date = datetime.now().date()
    logger.info(f"This VaR scheduler is running.-----------> {last_date}")
    if not VaR.objects.filter(date=last_date).exists():
            logger.info(f"This VaR scheduler is running.-----------> {last_date}")
            
            # Calculate and store VaR for each confidence level
            for confidence_level in confidence_levels:
                var_value = np.percentile(portfolio_returns, (1 - confidence_level) * 100)
                
                # Update or create the VaR record in the database
                VaR.objects.update_or_create(
                    date=last_date,
                    confidence_level=confidence_level,
                    defaults={'var_value': var_value}
                )

            logger.info("VaR values have been successfully updated or created.")
    else:
            logger.info(f"VaR values for {last_date} already exist.")


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

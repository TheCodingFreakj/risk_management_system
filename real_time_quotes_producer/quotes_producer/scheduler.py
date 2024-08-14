from datetime import datetime
import time
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
from contextlib import contextmanager

scheduler = BackgroundScheduler()

@contextmanager
def wait_for_django_server(url, timeout=120, initial_retry_interval=1):
    """Context manager to wait until the Django server at `url` is available or timeout occurs."""
    start_time = time.time()
    retry_interval = initial_retry_interval

    while time.time() - start_time < timeout:
        try:
            response = requests.post(url)
            if response.status_code == 200:
                print("Django server is up and running.")
                yield True  # Server is ready, proceed with scheduler
                return
        except ConnectionError:
            print(f"Django server is not ready yet, retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)  # Wait before retrying
            retry_interval = min(retry_interval * 2, 60)  # Exponential backoff with a max wait time of 60 seconds

    print("Django server did not start in time.")
    yield False  # Server did not start in time
def call_produce_to_kafka_viewset():
    url = 'http://127.0.0.1:8003/quotes_producer/stockdata/producetokafka/'
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.post(url)
            if response.status_code == 200:
                logger.info(f"Successfully called produce_to_kafka viewset: {response.json()}")
                break
            else:
                logger.error(f"Error: {response.status_code} - {response.text}")
        except requests.ConnectionError as e:
            logger.error(f"ConnectionError: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Failed to connect after {max_retries} attempts")



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

@contextmanager
def managed_scheduler():
    """Context manager to start and stop the scheduler."""
    scheduler = BackgroundScheduler()
    try:
        scheduler.start()
        logger.info("Scheduler started.")
        yield scheduler  # Yield control back to the block using this context
    except Exception as e:
        logger.error(f"Scheduler encountered an error: {e}")
    finally:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler stopped.")


def start_scheduler():
    server_url = 'http://127.0.0.1:8003/quotes_producer/stockdata/producetokafka/'  # Adjust as needed

    with wait_for_django_server(server_url) as server_ready:
        if server_ready:
            # Start the scheduler and add the job
            with managed_scheduler() as scheduler:
                try:
                    # Add the job to the scheduler
                    logger.info("Attempting to add job to scheduler.")
                    trigger = DateTrigger(run_date=None)  # `None` means "now"
                    scheduler.add_job(call_produce_to_kafka_viewset, trigger=trigger)
                    logger.info("Job added to scheduler.")
                except Exception as e:
                    logger.error(f"Failed to add job to scheduler: {e}")

                # Keep the scheduler running
                logger.info("Scheduler is now waiting for jobs.")
                try:
                    while True:  # Keep the scheduler alive
                        time.sleep(1)
                except (KeyboardInterrupt, SystemExit):
                    logger.info("Scheduler stopped manually.")
        else:
            logger.error("Failed to start scheduler as the Django server is not ready.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()

# Register the stop function to be called on application exit
atexit.register(stop_scheduler)

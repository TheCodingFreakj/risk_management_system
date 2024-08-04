import datetime
import json
import os
from django.core.management.base import BaseCommand

from ...models import StockPrice
from ...get_historic_data import fetch_historical_data,fetch_historic_data
from ...loggin_config import logger


class Command(BaseCommand):
    help = 'Starts the scheduler.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Scheduler started'))
        VANTAGE_API_KEY = os.getenv('VANTAGE_API_KEY', 'your_finnhub_api_key')
        USA_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        SYMBOLS = ['GOOGL', 'AMZN', 'TSLA','HSBA.L', 'BARC.L', 'VOD.L', 'BP.L', 'RDSA.L']
        # usa_historic_data = fetch_historical_data(USA_SYMBOLS, VANTAGE_API_KEY)
        # uk_historic_data = fetch_historical_data(UK_SYMBOLS, VANTAGE_API_KEY)


        for symbol in SYMBOLS:
            stock_data = fetch_historic_data(symbol)
            # us_data = fetch_historic_data(USA_SYMBOLS)
            logger.debug(f"The historic data total_historical_data -----------------> {stock_data}")
            # logger.debug(f"The historic data total_historical_data -----------------> {us_data}")

            if(stock_data.empty):
                return
                
            else:
                self.insert_to_db_Yfinance(stock_data)


           


        # if (uk_historic_data):
        #     uk_historic_data_1 = uk_historic_data
        #     logger.debug(f"The historic data total_historical_data -----------------> {uk_historic_data_1}")
        #     meta_data = uk_historic_data_1["Meta Data"]
        #     time_series = uk_historic_data_1["Time Series (Daily)"]
        #     symbol = meta_data["2. Symbol"]
        #     self.insert_to_db(meta_data, time_series, symbol)
        # if (usa_historic_data):
        #     usa_historic_data_1 = usa_historic_data
        #     meta_data = usa_historic_data_1["Meta Data"]
        #     time_series = usa_historic_data_1["Time Series (Daily)"]
        #     symbol = meta_data["2. Symbol"]
        #     self.insert_to_db(meta_data, time_series, symbol)
        #     # logger.debug(f"The historic data total_historical_data -----------------> {total_historical_data}")
    def insert_to_db_Yfinance(self, data):
        if data.empty:
            self.stdout.write(self.style.WARNING('No data found'))
            return

        stock_price_objects = []
        for index, row in data.iterrows():
            try:
                symbol = row['symbol']
                date = index.date()
                open_price = row['Open']
                high_price = row['High']
                low_price = row['Low']
                close_price = row['Close']
                volume = row['Volume']

                # Check if the record already exists
                if not StockPrice.objects.filter(symbol=symbol, date=date).exists():
                    stock_price = StockPrice(
                        symbol=symbol,
                        date=date,
                        open_price=open_price,
                        high_price=high_price,
                        low_price=low_price,
                        close_price=close_price,
                        volume=volume,
                    )
                    stock_price_objects.append(stock_price)
                else:
                    self.stdout.write(self.style.WARNING(f'Record for {symbol} on {date} already exists, skipping.'))

            except ValueError as e:
                self.stdout.write(self.style.ERROR(f'Error processing row for {symbol} on {date}: {e}'))

        # Batch insert all stock prices
        if stock_price_objects:
            StockPrice.objects.bulk_create(stock_price_objects)
            self.stdout.write(self.style.SUCCESS(f'Successfully inserted stock prices for {symbol}'))

    def insert_to_db(self, meta_data, time_series, symbol):
        for date_str, values in time_series.items():
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            open_price = float(values["1. open"])
            high_price = float(values["2. high"])
            low_price = float(values["3. low"])
            close_price = float(values["4. close"])
            volume = int(values["5. volume"])

            stock_price, created = StockPrice.objects.update_or_create(
                symbol=symbol,
                date=date,
                defaults={
                    'open_price': open_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'close_price': close_price,
                    'volume': volume
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully created stock price for {symbol} on {date}'))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully updated stock price for {symbol} on {date}'))

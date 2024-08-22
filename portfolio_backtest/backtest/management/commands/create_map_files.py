import csv
import pandas as pd
import yfinance as yf
import zipfile
import os
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create map files'

    def handle(self, *args, **kwargs):
        tickers = ["AMZN", "MSFT", "PG", "JNJ", "TSLA"]

        # Function to create map files
        def create_map_file(ticker, data):
            filename = f"{ticker.lower()}.csv"
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                # Assuming no ticker changes for simplicity
                for index, row in data.iterrows():
                    date = index.strftime('%Y-%m-%d')
                    writer.writerow([ticker, ticker, date])

        for ticker in tickers:
            # Fetch historical data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="max")
            
            # Create map file
            create_map_file(ticker, hist)

        print("Map files created for tickers:", tickers)
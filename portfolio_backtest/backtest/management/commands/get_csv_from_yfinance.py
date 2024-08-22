import yfinance as yf
import zipfile
import os
import pandas as pd

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create zip files'

    def handle(self, *args, **kwargs):

        # List of symbols to download
        symbols = ["AMZN", "MSFT", "PG", "JNJ", "TSLA"]

        # Directory where the zipped files will be saved
        output_dir = "./equity/usa/daily/"

        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        for symbol in symbols:
            # Download historical data for the symbol
            data = yf.download(symbol, start="1998-01-01", end="2024-07-31", interval="1d")
            
            # Rename the columns to match the required format: Date, Open, High, Low, Close, Volume
            data = data.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
            
            # Reset the index to get the Date as a column
            data = data.reset_index()
            
            # Convert Date to the format YYYYMMDD
            data["Date"] = data["Date"].dt.strftime('%Y%m%d')
            
            # Save the data to a CSV file
            csv_filename = f"{symbol.lower()}.csv"
            csv_filepath = os.path.join(output_dir, csv_filename)
            data.to_csv(csv_filepath, index=False, header=False)

            # Zip the CSV file
            zip_filename = f"{symbol.lower()}.zip"
            zip_filepath = os.path.join(output_dir, zip_filename)
            with zipfile.ZipFile(zip_filepath, "w") as zip_file:
                zip_file.write(csv_filepath, os.path.basename(csv_filepath))

            # Cleanup: Remove the CSV file after zipping
            os.remove(csv_filepath)
        print("All data has been downloaded, saved, and zipped.")

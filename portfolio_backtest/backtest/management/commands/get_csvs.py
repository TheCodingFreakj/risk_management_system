import pandas as pd
import yfinance as yf
import zipfile
import os
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Format zip files'

    def handle(self, *args, **kwargs):


        import requests
        import pandas as pd
        import os

        def fetch_corporate_actions(symbol, api_key):
                url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
                response = requests.get(url)
                if response.status_code == 200:
                    print(response.json())
                    return response.json()
                else:
                    print(f"Failed to fetch data for {symbol}: {response.status_code}, {response.text}")
                    return []

        def create_map_file(symbol, actions, output_dir):
                # List to store map file entries
                map_data = []
                
                # Process each corporate action
                for action in actions:
                    date = action['date'].replace("-", "")
                    status = "Z"  # Set status to "Z" as per your example
                    map_data.append((date, symbol.lower(), status))
                
                # Add the final row with a far future date
                map_data.append(("20501231", symbol.lower(), "Z"))
                
                # Convert to DataFrame and save as CSV
                df = pd.DataFrame(map_data, columns=["date", "ticker", "status"])
                csv_filename = f"{symbol.lower()}.csv"
                csv_filepath = os.path.join(output_dir, csv_filename)
                df.to_csv(csv_filepath, index=False, header=False)
                print(f"Map file created for {symbol}: {csv_filename}")

        # Example usage
        api_key = "cqjbehpr01qnjotffkq0cqjbehpr01qnjotffkqg"
        symbols = ["AMZN", "MSFT", "PG", "JNJ", "TSLA"]  # Add more symbols as needed
        output_dir = "./equity/usa/map_files/"

        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        for symbol in symbols:
            actions = fetch_corporate_actions(symbol, api_key)
            create_map_file(symbol, actions, output_dir)



        
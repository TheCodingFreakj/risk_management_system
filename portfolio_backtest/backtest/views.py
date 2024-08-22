import io
import os
import re
import tarfile
from django.http import JsonResponse
from backtest.management.commands.update_asset_data import Command as UpdateAssetDataCommand
import docker
def update_asset_data(request):
    """API endpoint to update asset data on demand."""
    UpdateAssetDataCommand().handle()
    return JsonResponse({"message": "Asset data updated successfully"})


# backtest/views.py

import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from backtest.models import BacktestConfig
from docker.errors import DockerException
def is_json_file_empty(file_path):
    # Check if the file exists and is not empty
    if not os.path.exists(file_path):
        print("File does not exist.")
        return True
    
    if os.path.getsize(file_path) == 0:
        print("File is empty (0 bytes).")
        return True
    
    # Check if the file contains only whitespace or is malformed
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()  # Strip out whitespace characters
            
            if not content:
                print("File contains only whitespace.")
                return True
            
            # Attempt to load the JSON to ensure it's not malformed
            json.loads(content)
            print("File is a valid JSON and not empty.")
            return False
        
    except json.JSONDecodeError:
        print("File is not a valid JSON.")
        return True
def generate_config(request, backtest_id):
    backtest_config = get_object_or_404(BacktestConfig, id=backtest_id)

        # Fetch assets related to the portfolio
    assets = backtest_config.portfolio.assets.all()

    # Prepare market_caps and volatilities dictionaries
    market_caps = {asset.symbol: asset.market_cap for asset in assets}
    volatilities = {asset.symbol: asset.volatility for asset in assets}
    # Step 2: Stringify the nested objects
    market_caps_str = json.dumps(market_caps)
    volatilities_str = json.dumps(volatilities)
    config = {
    "environment": "backtesting",
    "algorithm-type-name": "BacktestingAlgorithm",
    "algorithm-language": "Python",
    "algorithm-location": "/Lean/Algorithm.Python/BacktestingAlgorithm.py",
    "data-folder": "/Lean/Data",
    "debugging": False,
    "debugging-method": "LocalCmdLine",
    "log-handler": "ConsoleLogHandler",
    "messaging-handler": "QuantConnect.Messaging.Messaging",
    "job-queue-handler": "QuantConnect.Queues.JobQueue",
    "api-handler": "QuantConnect.Api.Api",
    "map-file-provider": "QuantConnect.Data.Auxiliary.LocalDiskMapFileProvider",
    "factor-file-provider": "QuantConnect.Data.Auxiliary.LocalDiskFactorFileProvider",
    "data-provider": "QuantConnect.Lean.Engine.DataFeeds.DefaultDataProvider",
    "object-store": "QuantConnect.Lean.Engine.Storage.LocalObjectStore",
    "data-aggregator": "QuantConnect.Lean.Engine.DataFeeds.AggregationManager",
    "symbol-minute-limit": 10000,
    "symbol-second-limit": 10000,
    "symbol-tick-limit": 10000,
    "show-missing-data-logs": True,
    "maximum-warmup-history-days-look-back": 5,
    "maximum-data-points-per-chart-series": 1000000,
    "maximum-chart-series": 30,
    "force-exchange-always-open": False,
    "transaction-log": "",
    "reserved-words-prefix": "@",
    "job-user-id": "0",
    "api-access-token": "",
    "job-organization-id": "",
    "log-level": "trace",
    "debug-mode": True,
    "results-destination-folder": f"/Lean/Results",
    "mute-python-library-logging": "False",
    "parameters": {
        "weighting_scheme": backtest_config.weighting_scheme,
        "rebalancing_frequency": backtest_config.rebalancing_frequency,
        "market_caps": market_caps_str,
        "volatilities": volatilities_str,
        "portfolio": json.dumps({
        "initial_capital": str(backtest_config.portfolio.initial_capital),
        "assets": list(assets.values_list("symbol", flat=True)),
       })
    },
    "python-additional-paths": [],
    "environments": {
        "backtesting": {
            "live-mode": False,
            "setup-handler": "QuantConnect.Lean.Engine.Setup.BacktestingSetupHandler",
            "result-handler": "QuantConnect.Lean.Engine.Results.BacktestingResultHandler",
            "data-feed-handler": "QuantConnect.Lean.Engine.DataFeeds.FileSystemDataFeed",
            "real-time-handler": "QuantConnect.Lean.Engine.RealTime.BacktestingRealTimeHandler",
            "history-provider": [
                "QuantConnect.Lean.Engine.HistoricalData.SubscriptionDataReaderHistoryProvider"
            ],
            "transaction-handler": "QuantConnect.Lean.Engine.TransactionHandlers.BacktestingTransactionHandler",
        }
    },
}

    local_config_path = "./config-algo2.json"
    print(f"Writing data to {local_config_path}")
    print("Data to be written:", config)
    write_json_config(config, local_config_path)
    
def write_json_config(config, local_config_path):
    try:
        # Ensure directory exists
        directory = os.path.dirname(local_config_path)
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist. Creating it...")
            os.makedirs(directory, exist_ok=True)

        # Debug: Check what is going to be written
        print("Attempting to write the following data to JSON:")
        
        # Convert the dictionary to a JSON string with indentation for readability
        json_data = json.dumps(config, indent=4)
        print(json_data)  # Print the config data in JSON format

        # Write the JSON data to a file
        with open(local_config_path, 'w') as json_file:
            json_file.write(json_data)
            print(f"Config file successfully written to {local_config_path}")
     
        
        # Debug: Check if the file was actually created and its size
        if os.path.exists(local_config_path):
            print(f"File {local_config_path} was created successfully.")
            print(f"File size: {os.path.getsize(local_config_path)} bytes")
        else:
            print(f"File {local_config_path} was not created.")

    except IOError as e:
        print(f"IOError while writing the config file: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")  

import subprocess
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def copy_file_to_container(src_path, container_name, dest_path):
    """Copy a file from the host to a Docker container using a tar archive."""
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        
        # Create a tar archive in memory
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            tar.add(src_path, arcname=os.path.basename(dest_path))
        
        tar_stream.seek(0)  # Rewind the file pointer to the start of the stream
        
        # Put the tar archive to the container
        success = container.put_archive(os.path.dirname(dest_path), tar_stream)
        
        if success:
            return True
        else:
            print(f"Failed to copy the file {src_path} to the container {container_name} at {dest_path}")
            return False

    except DockerException as e:
        print(f"Error copying file to container: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False



def extract_statistics_dict(data_list):
    statistics = {}
    # print(f"data_list------------------------>{data_list}")
    if data_list:
    #     # Split the string at newline characters
          log_lines = data_list.split('\n')
          
          for line in log_lines:
            print(f"log_lines------------------------>{line}")
            if line.startswith("STATISTICS::"):
                # Extract the entire statistics line after "STATISTICS::"
                match = re.search(r'STATISTICS::\s*(.*)', line)
                if match:
                    stat_line = match.group(1).strip()

                    # Split the stat_line into the stat name and stat value
                    if ' ' in stat_line:
                        stat_name, stat_value = stat_line.rsplit(' ', 1)
                        stat_name = stat_name.strip()
                        stat_value = stat_value.strip()

                        # Add to the dictionary
                        statistics[stat_name] = stat_value

    return statistics
@csrf_exempt
def run_backtest(request, backtest_id):
    # Generate the config file
    generate_config(request, backtest_id)
    config_path = "/Lean/config-algo2.json"
    local_config_path='./config-algo2.json'

    if not is_json_file_empty(local_config_path):
        print(copy_file_to_container(local_config_path,"portfoliobacktest", config_path))
       

        if(copy_file_to_container(local_config_path,"portfoliobacktest", config_path)):

            try:
                result = run_backtest_and_filter_logs(config_path)
                print(f"result---------> {result}")
                res = extract_statistics_dict(result)
                print(f"res ---------> {res}")
                 # If result is a dict, return it as JsonResponse
                if isinstance(result, dict):
                    return JsonResponse(res)
                
                # If result is not a dict, use safe=False
                return JsonResponse(res, safe=False)
            
            except subprocess.CalledProcessError as e:
                print(f"Subprocess error: {e.output}")
                print(f"Subprocess stderr: {e.stderr}")  # Print the stderr for more detailed error information
                return JsonResponse({"error": "Backtest failed", "output": e.output, "stderr": e.stderr}, status=500)
            
            except Exception as e:
                print(f"Unexpected error: {e}")
                return JsonResponse({"error": str(e)}, status=500)
        else:
           return JsonResponse({"error": "File cant be copied"}, status=500)     
    else:
        return JsonResponse({"error": "File is invalid"}, status=500)

def run_backtest_and_filter_logs(config_path):
    # Run the backtest
    process = subprocess.Popen(
        ["dotnet", "/Lean/QuantConnect.Lean.Launcher.dll", "--config", config_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    messages_logs_filtered = []

    # Filter the logs in real-time
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            # Filter out specific error
            if "System.InvalidOperationException: GIL must always be released" not in output:
                print(output.strip())  # Print the filtered log
                messages_logs_filtered.append(output.strip())
            else:
                print("Filtered out GIL error during shutdown.")  # Optionally log the filtering

    # Ensure to read stderr to avoid deadlocks
    for error in process.stderr:
        if "System.InvalidOperationException: GIL must always be released" not in error:
            print(error.strip())
        else:
            print("Filtered out GIL error during shutdown.")  # Optionally log the filtering

    return "\n".join(messages_logs_filtered)



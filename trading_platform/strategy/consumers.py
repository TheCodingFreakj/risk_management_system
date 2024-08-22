import io
import json
import os
import subprocess
import tarfile
import time
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import requests
import os
import json
import asyncio
import uuid
import requests
import subprocess
from channels.generic.websocket import AsyncWebsocketConsumer
import docker
from docker.errors import DockerException
import re

class BacktestConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = docker.from_env()  # Initialize Docker client
        self.is_execution_complete = False
        self.previous_results = None  # To store results of the previous execution
        self.logs = []

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        strategy_id = data.get('strategy_id')
        
        if strategy_id:
            await self.run_backtest(strategy_id)

    async def run_backtest(self, strategy_id):
        try:
            # Check if the execution is already complete
            if self.is_execution_complete:
                await self.send_message({
                    'success': True,
                    'data': self.previous_results,
                    'message': 'Backtest already completed, returning previous results.'
                })
                return

            # Get the strategy configuration
            strategy_data = await self.fetch_strategy_config(strategy_id)
            print(f"strategy_data--------------------------->{strategy_data}")
            if not strategy_data:
                return

            # Generate the config data for the backtest
            config_data = self.generate_config_data(strategy_data)
            
            # Write the config.json file to a temporary location
            temp_config_path = '/tmp/config.json'
            self.write_config(temp_config_path, config_data)
            
            # Copy the config.json into the Docker container
            container_name = 'lean-engine'
            config_file_path_in_container = '/Lean/config-algo1.json'
            if not await self.copy_file_to_container(temp_config_path, container_name, config_file_path_in_container):
                return

            # Run the Lean engine with the updated config.json
            if not await self.run_lean_engine(container_name):
                return

            self.is_execution_complete = True  # Set the flag after successful execution
            await self.send_message({'success': True, 'data': 'Backtest completed successfully.'})

        except Exception as e:
            await self.send_message({'success': False, 'error': f'An error occurred: {str(e)}'})

    async def fetch_strategy_config(self, strategy_id):
        """Fetch strategy configuration from an external service."""
        strategy_url = f"http://tradingplatform:8010/api/strategy/{strategy_id}/"
        response = await asyncio.to_thread(requests.get, strategy_url)
        if response.status_code == 200:
            return response.json()
        else:
            await self.send_message({'success': False, 'error': 'Strategy not found'})
            return None

    def generate_config_data(self, strategy_data):
        """Generate the configuration data for the backtest."""
        algorithm_name = strategy_data.get('name', 'DynamicMovingAverageAlgorithm')
        short_ma_period = strategy_data.get('short_ma_period')
        long_ma_period = strategy_data.get('long_ma_period')
        max_drawdown = strategy_data.get('max_drawdown')
        stock = strategy_data.get('stock')
        start_time = strategy_data.get('start_date')
        end_time = strategy_data.get('end_date')
        backtest_id = str(uuid.uuid4())
        return {
            "environment": "backtesting",
            "algorithm-type-name": algorithm_name,
            "algorithm-language": "Python",
            "algorithm-location": "Algorithm.Python/DynamicMovingAverageAlgorithm.py",
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
            "results-destination-folder":f"/Lean/Results/{backtest_id}",
            "mute-python-library-logging": "False",
            "parameters": {
                        "ShortMAPeriod": short_ma_period,
                        "LongMAPeriod": long_ma_period,
                        "StartDate": start_time,
                        "EndDate": end_time,
                        "InitialCash": max_drawdown,
                        "Stock": stock
                    },
            "python-additional-paths": [],
            "environments": {
                "backtesting": {
                    "live-mode": False,
                    "setup-handler": "QuantConnect.Lean.Engine.Setup.BacktestingSetupHandler",
                    "result-handler": "QuantConnect.Lean.Engine.Results.BacktestingResultHandler",
                    "data-feed-handler": "QuantConnect.Lean.Engine.DataFeeds.FileSystemDataFeed",
                    "real-time-handler": "QuantConnect.Lean.Engine.RealTime.BacktestingRealTimeHandler",
                    "history-provider": ["QuantConnect.Lean.Engine.HistoricalData.SubscriptionDataReaderHistoryProvider"],
                    "transaction-handler": "QuantConnect.Lean.Engine.TransactionHandlers.BacktestingTransactionHandler"
                }
            }
        }

       
    def write_config(self, path, data):
        """Helper method to write config to a file."""
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
  
    async def copy_file_to_container(self, src_path, container_name, dest_path):
        """Copy a file from the host to a Docker container using a tar archive."""
        try:
            container = self.client.containers.get(container_name)
            
            # Create a tar archive in memory
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                tar.add(src_path, arcname=os.path.basename(dest_path))
            
            tar_stream.seek(0)  # Rewind the file pointer to the start of the stream
            
            # Put the tar archive to the container
            container.put_archive(os.path.dirname(dest_path), tar_stream)
            return True
        except DockerException as e:
            await self.send_message({'success': False, 'error': f"Error copying config.json to container: {str(e)}"})
            return False
    async def run_lean_engine(self, container_name):
        """Run the Lean engine DLL inside the Docker container and return the result."""
        try:
            
            container = self.client.containers.get(container_name)
            exec_result = container.exec_run(
                'dotnet /Lean/QuantConnect.Lean.Launcher.dll',
                stdout=True,
                stderr=True,
                stream=True
            )

            # log_line = exec_result.output.decode().strip()
            time.sleep(2)
            for log in exec_result.output:
                log_line = log.decode('utf-8').strip()
                self.logs.append(log_line)
            time.sleep(2)    
            # Optionally: Check container logs again to see if anything was missed
            additional_logs = container.logs().decode('utf-8').strip().splitlines()
                
            for log_line in additional_logs:
                self.logs.append(log_line)
            
            # Combine all logs into a single string (if needed)
            full_log = "\n".join(self.logs)
            # Adjust this based on the WebSocket server's limits
            # Split the full log into chunks
            chunk_size = 1000  
            chunks = [full_log[i:i+chunk_size] for i in range(0, len(full_log), chunk_size)]
            # Optional: Small delay to avoid overwhelming the WebSocket server
            # Send each chunk separately
            for i, chunk in enumerate(chunks):
                message = {
                    'success': True,
                    'data': chunk,
                    'last_chunk': i == len(chunks) - 1  # Set this to True for the last chunk
                }
                await self.send_message(message)
                await asyncio.sleep(0.1)  
        except DockerException as e:
            await self.send_message({'success': False, 'error': f"Error running Lean engine: {str(e)}"})
            return False
    async def send_message(self, message):
        """Helper method to send a message over WebSocket."""
        await self.send(json.dumps(message))

   

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
            config_file_path_in_container = '/Lean/config.json'
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
    def capture_logs_with_timeout(self,container_name, timeout=10):
        client = docker.from_env()
        container = client.containers.get(container_name)
        
        log_stream = container.logs(stream=True)
        last_log_time = time.time()

        print(f"log_stream found: {log_stream}")
        
        try:
            # for log in log_stream:
            #     log_line = log.decode('utf-8').strip()
            #     print(f"Captured Log: {log_line}")
                
                # Process the log line (e.g., check for "STATISTICS::")
                if "STATISTICS::" in log_stream:
                    print(f"Statistics found: {log_stream}")
                
                # Reset the timer since we received a new log
                # last_log_time = time.time()
                
                # # If we want to exit the loop based on a specific condition:
                # if self.some_condition_based_on_log(log_line):
                #     break
                
                # # Check if the log stream has been quiet for longer than the timeout
                # if time.time() - last_log_time > timeout:
                #     print("No logs received for the timeout duration, stopping.")
                #     break
        except Exception as e:
            print(f"An error occurred while capturing logs: {str(e)}")


    def some_condition_based_on_log(self,log_line):
        # Example condition to exit early (customize as needed)
        return "Analysis Complete" in log_line           


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
            
            await self.send_message({'success': True, 'data': self.logs})

        except DockerException as e:
            await self.send_message({'success': False, 'error': f"Error running Lean engine: {str(e)}"})
            return False
    async def send_message(self, message):
        """Helper method to send a message over WebSocket."""
        await self.send(json.dumps(message))


    async def parse_stdout_output(self, stdout_output):
        """Parse the stdout output to extract relevant information."""
        output_lines = stdout_output.splitlines()
        parsed_data = {}

        print(f"total output_lines-------------------->{output_lines}")
        
        for line in output_lines:
            print(f"outer output_lines------------------------> {line}")
            
            if "STATISTICS::" in line:
                print(f"output_lines------------------------> {line}")
                # Extract the entire statistics line after "STATISTICS::"
                match = re.search(r'STATISTICS::\s*(.*)', line)
                
                if match:
                    stat_line = match.group(1).strip()

                    # Split the stat_line into the stat name and stat value
                    if ' ' in stat_line:
                        stat_name, stat_value = stat_line.rsplit(' ', 1)
                        stat_name = stat_name.strip()
                        stat_value = stat_value.strip()

                        # Handle multiple occurrences by appending to a list
                        if stat_name in parsed_data:
                            if isinstance(parsed_data[stat_name], list):
                                parsed_data[stat_name].append(stat_value)
                            else:
                                parsed_data[stat_name] = [parsed_data[stat_name], stat_value]
                        else:
                            parsed_data[stat_name] = stat_value
        
        return json.dumps(parsed_data)




    async def send_message(self, message):
        """Helper method to send a message over WebSocket."""
        await self.send(json.dumps(message))    


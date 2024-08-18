import io
import json
import os
import subprocess
import tarfile
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

class BacktestConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = docker.from_env()  # Initialize Docker client

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
            # Get the strategy configuration
            strategy_data = await self.fetch_strategy_config(strategy_id)
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
        start_date = strategy_data.get('start_date', '2024-01-01')
        end_date = strategy_data.get('end_date', '2024-06-01')
        short_ma_period = strategy_data.get('short_ma_period')
        long_ma_period = strategy_data.get('long_ma_period')
        max_drawdown = strategy_data.get('max_drawdown')
        stock = strategy_data.get('stock')
        backtest_id = str(uuid.uuid4())

        return {
            "environment": "backtesting",
            "algorithm-type-name": algorithm_name,
            "algorithm-language": "Python",
            "data-folder": "/Lean/Data",
            "result-handler": "QuantConnect.Lean.Engine.Results.BacktestingResultHandler",
            "real-time-handler": "QuantConnect.Lean.Engine.RealTime.BacktestingRealTimeHandler",
            "transaction-handler": "QuantConnect.Lean.Engine.TransactionHandlers.BacktestingTransactionHandler",
            "data-feed-handler": "QuantConnect.Lean.Engine.DataFeeds.FileSystemDataFeed",
            "setup-handler": "QuantConnect.Lean.Engine.Setup.BacktestingSetupHandler",
            "results-destination-folder": f"/app/Lean/Results/{backtest_id}",
            "plugin-directory": "/Lean/Plugins",
            "composer-dll-directory": "/Lean",
            "log-handler": "CompositeLogHandler",
            "job-queue-handler": "QuantConnect.Queues.JobQueue",
            "algorithm-location": "/Lean/Algorithm.Python/DynamicMovingAverageAlgorithm.py",
            "api-handler": "QuantConnect.Api.Api",
            "api-access-token": "",
            "job-organization-id": "",
            "messaging-handler": "QuantConnect.Messaging.Messaging",  
            "version-id": "1.0", 
            "cache-location": "/Lean/Cache",
            "lean-manager-type": "LocalLeanManager",
            "parameters": {
                "ShortMAPeriod": short_ma_period,
                "LongMAPeriod": long_ma_period,
                "StartDate": start_date,
                "EndDate": end_date,
                "InitialCash": max_drawdown,
                "Stock": stock
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
        """Run the Lean engine DLL inside the Docker container."""
        try:
            container = self.client.containers.get(container_name)
            exec_result = container.exec_run(
                'dotnet /Lean/QuantConnect.Lean.Launcher.dll',
                stdout=True,
                stderr=True
            )

            if exec_result.exit_code != 0:
                error_message = exec_result.output.decode().strip()
                await self.send_message({'success': False, 'error': error_message})
                return False
            return True
        except DockerException as e:
            await self.send_message({'success': False, 'error': f"Error running Lean engine: {str(e)}"})
            return False
    async def send_message(self, message):
        """Helper method to send a message over WebSocket."""
        await self.send(json.dumps(message))


import json
import os
import subprocess
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import requests

class BacktestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        strategy_id = data.get('strategy_id')
        
        if strategy_id:
            # Start the backtest process asynchronously
            await self.run_backtest(strategy_id)
 
    async def run_backtest(self, strategy_id):
        try:
            # External service URL to get strategy configuration
            strategy_url = f"http://tradingplatform:8010/api/strategy/{strategy_id}/"
            
            # Fetch the strategy configuration from the external service asynchronously
            response = await asyncio.to_thread(requests.get, strategy_url)
            if response.status_code == 200:
                strategy_data = response.json()
            else:
                await self.send_message({'success': False, 'error': 'Strategy not found'})
                return

            # Extract strategy details
            algorithm_name = strategy_data.get('name', 'MovingAverageCrossAlgorithm')
            start_date = strategy_data.get('start_date', '2024-01-01')
            end_date = strategy_data.get('end_date', '2024-06-01')
            short_ma_period = strategy_data.get('short_ma_period')
            long_ma_period = strategy_data.get('long_ma_period')
            max_drawdown = strategy_data.get('max_drawdown')

            # Generate a unique identifier for the backtest
            backtest_id = str(uuid.uuid4())

            config_data = {
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
    "algorithm-location": "/Lean/Algorithm.Python/MovingAverageCrossAlgorithm.py",
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
                    "InitialCash": max_drawdown
    }
}
           

             # Write the config.json file
           # Update the config file path to the new location
            config_file_path = os.path.join('/Lean', 'config.json')

            # Sample function to update config.json

            with open(config_file_path, 'w') as config_file:
                json.dump(config_data, config_file, indent=4)
            
            container_name = 'lean-engine'
            exec_command = [
        'docker', 'exec', container_name, 'dotnet', '/Lean/QuantConnect.Lean.Launcher.dll'
            ]

            result = None
            try:
                result = await asyncio.to_thread(subprocess.run, exec_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                print("Return code:", result.returncode)
                print("stdout:", result.stdout)
                print("stderr:", result.stderr)
                if result.returncode != 0:
                    print(f"Error running docker-compose: {result.stderr}")
                else:
                    print(f"docker-compose output: {result.stdout}")
            except FileNotFoundError as e:
                print(f"File not found error: {str(e)}")
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
            # # Run the Lean Engine backtest asynchronously
            # command = ['dotnet', 'run', '--project', "/app/Lean/Launcher/QuantConnect.Lean.Launcher.csproj", "--config", config_file_path]
            

            # Check for errors in running the backtest
            if result.returncode != 0:
                await self.send_message({'success': False, 'error': result.stderr.strip()})
                return

            # Process the result, assuming output is in JSON format
            output = result.stdout
            try:
                backtest_results = json.loads(output)
                await self.send_message({'success': True, 'data': backtest_results})
            except json.JSONDecodeError:
                await self.send_message({'success': False, 'error': 'Failed to parse backtest results.'})
        except Exception as e:
            await self.send_message({'success': False, 'error': f'An error occurred: {str(e)}'})

    def write_config(self, path, data):
        """Helper method to write config to a file."""
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    async def send_message(self, message):
        """Helper method to send a message over WebSocket."""
        await self.send(json.dumps(message))

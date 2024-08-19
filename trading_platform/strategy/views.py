import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import StrategyConfig, BacktestResult
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from .models import StrategyConfig
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import subprocess
import os
class StrategyConfigDetail(APIView):
    def get(self, request, strategy_id):
        try:
               
            strategy = StrategyConfig.objects.get(id=strategy_id)
            strategy_data = {
        "id": strategy.id,
        "name": strategy.name,
        "stock": strategy.stock,
        "short_ma_period": strategy.short_ma_period,
        "long_ma_period": strategy.long_ma_period,
        "stop_loss": strategy.stop_loss,
        "take_profit": strategy.take_profit,
        "max_drawdown": strategy.max_drawdown,
        "created_at": strategy.created_at,
        "updated_at": strategy.updated_at,
        'start_date':strategy.start_date,
        'end_date':strategy.end_date
    }

            return Response(strategy_data, status=status.HTTP_200_OK)
        except StrategyConfig.DoesNotExist:
            return Response({'error': 'Strategy not found'}, status=status.HTTP_404_NOT_FOUND)

class BacktestResultDetail(APIView):
    def get(self, request, result_id):
        try:
            result = BacktestResult.objects.get(id=result_id)
            
            data = {
                'equity_curve': result.equity_curve,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'total_return': result.total_return,
                'start_date': result.start_date,
                'end_date': result.end_date,
            }
            return Response(data, status=status.HTTP_200_OK)
        except BacktestResult.DoesNotExist:
            return Response({'error': 'Backtest result not found'}, status=status.HTTP_404_NOT_FOUND)


def home(request):
    return HttpResponse("Welcome to the Trading Platform API")





# @csrf_exempt  # Disable CSRF protection for this view if needed
# @require_POST  # Ensure that this view only handles POST requests
# def run_backtest_backend(request):
#     print(f"It is reaching here--------------------------->{json.loads(request.body)}")
   
#     try:
#             print(f"Received request data: {json.loads(request.body)}")
#             config_data = json.loads(request.body)
#             # # Save the configuration file
#             # if 'config_file' not in request.FILES:
#             #     return JsonResponse({'success': False, 'error': 'No configuration file provided'}, status=400)
        
#             # config_file = request.FILES['config_file']
#             # # Compute the path two directories up
#             base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#             config_file_path = os.path.join(base_dir, 'Lean', 'config.json')
#             print(config_file_path)
#             with open(config_file_path, 'w') as f:
#                 json.dump(config_data, f, indent=4)
#             # # Print the path to verify
#             # print(f"Config file path: {config_file_path}")
#             # print(f"config_file path: {config_file}")
#             # with open(config_file_path, 'wb') as f:
#             #     for chunk in config_file.chunks():
#             #         f.write(chunk)
            

#             command = ['dotnet', 'run','--project', "/app/Lean/Launcher/QuantConnect.Lean.Launcher.csproj", "--config", config_file_path]
#             # Run the Lean Engine backtest
#             # command = ['dotnet', 'run', '--project', '/app/Lean/Launcher/QuantConnect.Lean.Launcher.csproj', '--', '--config', config_file_path]

#             result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

#             # Check for errors in running the backtest
#             if result.returncode != 0:
#                 return JsonResponse({'success': False, 'error': result.stderr.strip()}, status=500)

#             # Process the result, assuming output is in JSON format
#             output = result.stdout
#             try:
#                 backtest_results = json.loads(output)
#             except json.JSONDecodeError:
#                 return JsonResponse({'success': False, 'error': 'Failed to parse backtest results.'}, status=500)

#             return JsonResponse(backtest_results)
        
#     except Exception as e:
#             return JsonResponse({'success': False, 'error': f'An error occurred from run_backtest_backend: {str(e)}'}, status=500)
    
   

# def api_strategy_detail(request, strategy_id):
#     strategy = get_object_or_404(StrategyConfig, id=strategy_id)

#     strategy_data = {
#         "id": strategy.id,
#         "name": strategy.name,
#         "stock": strategy.stock,
#         "short_ma_period": strategy.short_ma_period,
#         "long_ma_period": strategy.long_ma_period,
#         "stop_loss": strategy.stop_loss,
#         "take_profit": strategy.take_profit,
#         "max_drawdown": strategy.max_drawdown,
#         "created_at": strategy.created_at,
#         "updated_at": strategy.updated_at,
#         'start_date':strategy.start_date,
#         'end_date':strategy.end_date
#     }

#     return JsonResponse(strategy_data)



@csrf_exempt
def store_strategy(request):
    print(f"request.POST.get('short_ma_period'), {request.POST.get('short_ma_period')}")
    if request.method == 'POST':

        print(request.POST.get('name'))

        # Extract the parameters sent from Service A
        name = request.POST.get('name')
        stock = request.POST.get('stock')
        short_ma_period = request.POST.get('short_ma_period')
        long_ma_period = request.POST.get('long_ma_period')
        stop_loss = request.POST.get('stop_loss')
        take_profit = request.POST.get('take_profit')
        max_drawdown = request.POST.get('max_drawdown')
        end_date = request.POST.get('end_date')
        start_date = request.POST.get('start_date')
        # Create and save the strategy in the database
        strategy = StrategyConfig(
            name=name,
            short_ma_period=short_ma_period,
            long_ma_period=long_ma_period,
            stop_loss=stop_loss,
            take_profit=take_profit,
            max_drawdown=max_drawdown,
            stock=stock,
            start_date=start_date,
            end_date=end_date
        )
        strategy.save()

        return JsonResponse({'status': 'success', 'message': 'Strategy stored successfully'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)



def backtests_list(request, strategy_id):
    # Get the strategy object or return 404 if it doesn't exist
    strategy = get_object_or_404(StrategyConfig, id=strategy_id)
    
    # Get all backtests related to this strategy
    backtests = strategy.backtests.all()

    # Prepare the data to return
    backtests_data = [
        {
            "id": backtest.id,
            "start_date": backtest.start_date,
            "end_date": backtest.end_date,
            "total_return": backtest.total_return,
            "sharpe_ratio": backtest.sharpe_ratio
        }
        for backtest in backtests
    ]

    # Return the data as JSON
    return JsonResponse(backtests_data, safe=False)



@csrf_exempt
def save_backtest(request):
    if request.method == 'POST':
        data = request.json()
        
        # Extract the data from the request
        strategy_id = data.get("strategy_id")
        equity_curve = data.get("equity_curve")
        sharpe_ratio = data.get("sharpe_ratio")
        max_drawdown = data.get("max_drawdown")
        total_return = data.get("total_return")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Save the backtest result in the external service's database
        result = BacktestResult(
            strategy_id=strategy_id,
            equity_curve=equity_curve,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            total_return=total_return,
            start_date=start_date,
            end_date=end_date,
        )
        result.save()

        # Return the ID of the saved result
        return JsonResponse({"result_id": result.id}, status=200)

    return JsonResponse({"error": "Invalid request method"}, status=400)
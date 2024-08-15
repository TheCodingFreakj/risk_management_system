from django.urls import path
from .views import StrategyConfigDetail, run_backtest, BacktestResultDetail, api_strategy_detail, backtests_list, save_backtest, store_strategy

urlpatterns = [
    path('run_backtest/', run_backtest, name='run_backtest'),
    path('api/strategy/<int:strategy_id>/', api_strategy_detail, name='api_strategy_detail'),
    path('api/save_backtest/', save_backtest, name='save_backtest'),
    path('store_strategy/', store_strategy, name='store_strategy'),
    path('api/strategy/<int:strategy_id>/backtests/', backtests_list, name='backtests_list'),
    path('api/strategy/<int:strategy_id>/', StrategyConfigDetail.as_view(), name='strategy_detail'),
    path('api/backtest/<int:result_id>/', BacktestResultDetail.as_view(), name='backtest_detail'),
]
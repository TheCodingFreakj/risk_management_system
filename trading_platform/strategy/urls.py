from django.urls import path

from . import routing
from .views import StrategyConfigDetail,home, BacktestResultDetail, api_strategy_detail, backtests_list, save_backtest, store_strategy



urlpatterns = [
    path('', home, name='home'),
    # path('run_backtest_backend/', run_backtest_backend, name='run_backtest_backend'),
    path('api/strategy/<int:strategy_id>/', api_strategy_detail, name='api_strategy_detail'),
    path('api/save_backtest/', save_backtest, name='save_backtest'),
    path('store_strategy/', store_strategy, name='store_strategy'),
    path('api/strategy/<int:strategy_id>/backtests/', backtests_list, name='backtests_list'),
    path('api/strategy/<int:strategy_id>/', StrategyConfigDetail.as_view(), name='strategy_detail'),
    path('api/backtest/<int:result_id>/', BacktestResultDetail.as_view(), name='backtest_detail'),
]

# Include the WebSocket URLs
urlpatterns += routing.websocket_urlpatterns
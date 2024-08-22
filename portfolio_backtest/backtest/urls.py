from django.urls import path
from . import views

urlpatterns = [
    path('update-asset-data/', views.update_asset_data, name='update_asset_data'),
    path('run-backtest/<int:backtest_id>/', views.run_backtest, name='run_backtest'),
]
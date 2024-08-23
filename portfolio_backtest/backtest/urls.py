from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('show-results/', views.show_results, name='show_results'),
    path('update-asset-data/', views.update_asset_data, name='update_asset_data'),
    path('runbacktest/<int:backtest_id>/', views.run_backtest, name='runbacktest'),
]